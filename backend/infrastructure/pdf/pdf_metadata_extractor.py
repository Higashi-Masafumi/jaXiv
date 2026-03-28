from logging import getLogger
from pathlib import Path

import fitz

from domain.entities.pdf_paper import PdfPaperMetadata
from domain.errors.domain_error import PdfProcessingError
from domain.gateways.i_pdf_metadata_extractor import IPdfMetadataExtractor


class PdfMetadataExtractor(IPdfMetadataExtractor):
	"""Extracts title, authors and abstract from a PDF using PyMuPDF."""

	def __init__(self) -> None:
		self._logger = getLogger(__name__)

	def extract_metadata(self, pdf_path: Path) -> PdfPaperMetadata:
		"""Extract metadata from a PDF file.

		Attempts to read embedded metadata first; falls back to first-page
		heuristics (largest-font text as title) when the embedded fields are empty.
		"""
		try:
			doc = fitz.open(pdf_path)
		except Exception as e:
			raise PdfProcessingError(f'Failed to open PDF: {e}') from e

		try:
			meta = doc.metadata or {}
			title = (meta.get('title') or '').strip()
			author_raw = (meta.get('author') or '').strip()
			authors = [a.strip() for a in author_raw.split(',') if a.strip()]

			if not title and len(doc) > 0:
				title = self._extract_title_from_first_page(doc[0])

			if not title:
				title = pdf_path.stem

			self._logger.info('Extracted metadata: title=%r, authors=%d', title, len(authors))
			return PdfPaperMetadata(title=title, authors=authors, summary='')
		finally:
			doc.close()

	@staticmethod
	def _extract_title_from_first_page(page: fitz.Page) -> str:
		"""Heuristic: collect the text rendered in the largest font on page 1.

		Multiple spans sharing the same max font size are joined so that
		multi-line titles are captured correctly.
		"""
		try:
			blocks = page.get_text('dict')['blocks']
		except Exception:
			return ''

		# Gather (size, text) pairs from all text spans
		spans: list[tuple[float, str]] = []
		for block in blocks:
			if block.get('type') != 0:
				continue
			for line in block.get('lines', []):
				for span in line.get('spans', []):
					text = span.get('text', '').strip()
					size = float(span.get('size', 0))
					if text and size > 0:
						spans.append((size, text))

		if not spans:
			return ''

		max_size = max(s for s, _ in spans)
		title_parts = [t for s, t in spans if s >= max_size - 0.5]
		return ' '.join(title_parts)
