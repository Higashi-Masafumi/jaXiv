import io
import re
from logging import getLogger
from pathlib import Path
from typing import ClassVar

import cv2
import fitz
import numpy as np
import onnxruntime as ort
from PIL import Image

from domain.entities.figure import ExtractedFigure
from domain.errors.extraction_error import FigureExtractionError
from domain.gateways.figure_extractor import FigureExtractorGateway

FIGURE_NUMBER_RE: re.Pattern[str] = re.compile(
    r"(?:Fig(?:ure)?|図)\s*\.?\s*(\d+)", re.IGNORECASE
)


class PdfFigureExtractor(FigureExtractorGateway):
    """Extracts figures and captions from PDFs using DocLayout-YOLO (ONNX) and PyMuPDF."""

    RENDER_DPI: ClassVar[int] = 150
    CONFIDENCE_THRESHOLD: ClassVar[float] = 0.3
    CAPTION_DISTANCE_RATIO: ClassVar[float] = 0.20
    MAX_FIGURES: ClassVar[int] = 20
    IMGSZ: ClassVar[int] = 1024
    PAD_COLOR: ClassVar[tuple[int, int, int]] = (114, 114, 114)
    FIGURE_CLASS_ID: ClassVar[int] = 3
    FIGURE_CAPTION_CLASS_ID: ClassVar[int] = 4

    def __init__(self, session: ort.InferenceSession) -> None:
        self._logger = getLogger(__name__)
        self._session = session

    def extract_figures(self, pdf_path: Path) -> list[ExtractedFigure]:
        """Extract figures with captions from a PDF file."""
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            raise FigureExtractionError(f"Failed to open PDF: {e}") from e

        scale = self.RENDER_DPI / 72.0
        all_figures: list[ExtractedFigure] = []

        try:
            for page_num in range(len(doc)):
                if len(all_figures) >= self.MAX_FIGURES:
                    break

                page = doc[page_num]

                pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
                page_img = Image.open(io.BytesIO(pix.tobytes("png")))

                img_bgr = cv2.cvtColor(np.array(page_img), cv2.COLOR_RGB2BGR)
                h, w = img_bgr.shape[:2]
                ratio = min(self.IMGSZ / h, self.IMGSZ / w)
                new_w, new_h = int(round(w * ratio)), int(round(h * ratio))
                img_bgr = cv2.resize(
                    img_bgr, (new_w, new_h), interpolation=cv2.INTER_LINEAR
                )
                pad_w = (self.IMGSZ - new_w) // 2
                pad_h = (self.IMGSZ - new_h) // 2
                img_bgr = cv2.copyMakeBorder(
                    img_bgr,
                    pad_h,
                    self.IMGSZ - new_h - pad_h,
                    pad_w,
                    self.IMGSZ - new_w - pad_w,
                    cv2.BORDER_CONSTANT,
                    value=self.PAD_COLOR,
                )
                blob = img_bgr.transpose(2, 0, 1)[np.newaxis].astype(np.float32) / 255.0

                preds = self._session.run(None, {"images": blob})[0][0]
                figure_bboxes: list[list[float]] = []
                caption_bboxes: list[list[float]] = []
                for det in preds:
                    if det[4] <= self.CONFIDENCE_THRESHOLD:
                        continue
                    bbox = [
                        float((det[0] - pad_w) / ratio),
                        float((det[1] - pad_h) / ratio),
                        float((det[2] - pad_w) / ratio),
                        float((det[3] - pad_h) / ratio),
                    ]
                    if int(det[5]) == self.FIGURE_CLASS_ID:
                        figure_bboxes.append(bbox)
                    elif int(det[5]) == self.FIGURE_CAPTION_CLASS_ID:
                        caption_bboxes.append(bbox)

                threshold = page.rect.height * scale * self.CAPTION_DISTANCE_RATIO
                used_captions: set[int] = set()
                associations: list[tuple[list[float], list[float] | None]] = []
                for fig_bbox in figure_bboxes:
                    best_cap_idx: int | None = None
                    best_dist = float("inf")
                    for cap_idx, cap_item in enumerate(caption_bboxes):
                        if cap_idx in used_captions:
                            continue
                        dist = (
                            abs(cap_item[1] - fig_bbox[3])
                            if cap_item[1] >= fig_bbox[1]
                            else abs(fig_bbox[1] - cap_item[3]) + threshold * 0.1
                        )
                        if dist < best_dist and dist < threshold:
                            best_dist, best_cap_idx = dist, cap_idx
                    if best_cap_idx is not None:
                        used_captions.add(best_cap_idx)
                        associations.append((fig_bbox, caption_bboxes[best_cap_idx]))
                    else:
                        associations.append((fig_bbox, None))

                for fig_bbox, cap_bbox in associations:
                    if len(all_figures) >= self.MAX_FIGURES:
                        break

                    buf = io.BytesIO()
                    page_img.crop(
                        (
                            int(fig_bbox[0]),
                            int(fig_bbox[1]),
                            int(fig_bbox[2]),
                            int(fig_bbox[3]),
                        )
                    ).save(buf, format="PNG")

                    caption_text = ""
                    figure_number = None
                    if cap_bbox is not None:
                        pdf_rect = fitz.Rect(
                            cap_bbox[0] / scale,
                            cap_bbox[1] / scale,
                            cap_bbox[2] / scale,
                            cap_bbox[3] / scale,
                        )
                        caption_text = " ".join(
                            page.get_text("text", clip=pdf_rect).strip().split()
                        )
                        if m := FIGURE_NUMBER_RE.search(caption_text):
                            figure_number = int(m.group(1))

                    all_figures.append(
                        ExtractedFigure(
                            image_bytes=buf.getvalue(),
                            caption=caption_text,
                            figure_number=figure_number,
                            page_number=page_num + 1,
                        )
                    )
        finally:
            doc.close()

        self._logger.info(
            "Extracted %d figures from %s", len(all_figures), pdf_path.name
        )
        return all_figures
