import io
import re
from logging import getLogger
from pathlib import Path
from typing import ClassVar

import fitz
from doclayout_yolo import YOLOv10
from huggingface_hub import hf_hub_download
from PIL import Image

from domain.entities.extracted_figure import ExtractedFigure
from domain.errors.domain_error import PdfProcessingError
from domain.gateways import IPdfFigureExtractor

FIGURE_NUMBER_RE: re.Pattern[str] = re.compile(r'(?:Fig(?:ure)?|図)\s*\.?\s*(\d+)', re.IGNORECASE)


class PdfFigureExtractor(IPdfFigureExtractor):
	"""Extracts figures and captions from PDFs using DocLayout-YOLO and PyMuPDF.

	Requires model weights to be pre-downloaded via scripts/download_models.py.
	"""

	RENDER_DPI: ClassVar[int] = 200
	CONFIDENCE_THRESHOLD: ClassVar[float] = 0.3
	CAPTION_DISTANCE_RATIO: ClassVar[float] = 0.20
	MAX_FIGURES: ClassVar[int] = 20
	FIGURE_CLASS: ClassVar[str] = 'figure'
	FIGURE_CAPTION_CLASS: ClassVar[str] = 'figure_caption'

	def __init__(
		self,
		hf_repo_id: str = 'juliozhao/DocLayout-YOLO-DocStructBench',
		hf_filename: str = 'doclayout_yolo_docstructbench_imgsz1024.pt',
	) -> None:
		self._logger = getLogger(__name__)
		self._hf_repo_id = hf_repo_id
		self._hf_filename = hf_filename
		self._model: YOLOv10 | None = None

	@property
	def model(self) -> YOLOv10:
		if self._model is None:
			model_path = hf_hub_download(repo_id=self._hf_repo_id, filename=self._hf_filename)
			self._model = YOLOv10(model_path)
		return self._model

	def extract_figures(self, pdf_path: Path) -> list[ExtractedFigure]:
		"""Extract figures with captions from a PDF file."""
		try:
			doc = fitz.open(pdf_path)
		except Exception as e:
			raise PdfProcessingError(f'Failed to open PDF: {e}') from e

		scale = self.RENDER_DPI / 72.0
		all_figures: list[ExtractedFigure] = []

		try:
			for page_num in range(len(doc)):
				if len(all_figures) >= self.MAX_FIGURES:
					break

				page = doc[page_num]
				page_height = page.rect.height * scale

				mat = fitz.Matrix(scale, scale)
				pix = page.get_pixmap(matrix=mat)
				img_bytes = pix.tobytes('png')
				page_img = Image.open(io.BytesIO(img_bytes))

				det_res = self.model.predict(
					page_img,
					imgsz=1024,
					conf=self.CONFIDENCE_THRESHOLD,
					device='cpu',
					verbose=False,
				)

				figure_bboxes: list[list[float]] = []
				caption_bboxes: list[list[float]] = []

				for result in det_res:
					for i in range(len(result.boxes)):
						cls_name = result.names[int(result.boxes.cls[i])]
						bbox = result.boxes.xyxy[i].tolist()
						if cls_name == self.FIGURE_CLASS:
							figure_bboxes.append(bbox)
						elif cls_name == self.FIGURE_CAPTION_CLASS:
							caption_bboxes.append(bbox)

				associations = self._associate_captions(figure_bboxes, caption_bboxes, page_height)

				for fig_bbox, cap_bbox in associations:
					if len(all_figures) >= self.MAX_FIGURES:
						break

					cropped = page_img.crop(
						(int(fig_bbox[0]), int(fig_bbox[1]), int(fig_bbox[2]), int(fig_bbox[3]))
					)
					buf = io.BytesIO()
					cropped.save(buf, format='PNG')
					figure_bytes = buf.getvalue()

					caption_text = ''
					figure_number = None
					if cap_bbox is not None:
						pdf_rect = fitz.Rect(
							cap_bbox[0] / scale,
							cap_bbox[1] / scale,
							cap_bbox[2] / scale,
							cap_bbox[3] / scale,
						)
						caption_text = page.get_text('text', clip=pdf_rect).strip()
						caption_text = ' '.join(caption_text.split())
						match = FIGURE_NUMBER_RE.search(caption_text)
						if match:
							figure_number = int(match.group(1))

					all_figures.append(
						ExtractedFigure(
							image_bytes=figure_bytes,
							caption=caption_text,
							figure_number=figure_number,
							page_number=page_num + 1,
						)
					)
		finally:
			doc.close()

		self._logger.info('Extracted %d figures from %s', len(all_figures), pdf_path.name)
		return all_figures

	@staticmethod
	def _associate_captions(
		figure_bboxes: list[list[float]],
		caption_bboxes: list[list[float]],
		page_height: float,
	) -> list[tuple[list[float], list[float] | None]]:
		"""Associate each figure with its nearest caption using spatial proximity.

		Prefers captions below the figure, falls back to above.
		Uses greedy 1:1 matching.
		"""
		threshold = page_height * PdfFigureExtractor.CAPTION_DISTANCE_RATIO
		used_captions: set[int] = set()
		associations: list[tuple[list[float], list[float] | None]] = []

		for fig_bbox in figure_bboxes:
			fig_bottom = fig_bbox[3]
			fig_top = fig_bbox[1]
			best_cap_idx: int | None = None
			best_dist = float('inf')

			for cap_idx, cap_bbox in enumerate(caption_bboxes):
				if cap_idx in used_captions:
					continue
				cap_top = cap_bbox[1]

				if cap_top >= fig_top:
					dist = abs(cap_top - fig_bottom)
				else:
					dist = abs(fig_top - cap_bbox[3]) + threshold * 0.1

				if dist < best_dist and dist < threshold:
					best_dist = dist
					best_cap_idx = cap_idx

			if best_cap_idx is not None:
				used_captions.add(best_cap_idx)
				associations.append((fig_bbox, caption_bboxes[best_cap_idx]))
			else:
				associations.append((fig_bbox, None))

		return associations
