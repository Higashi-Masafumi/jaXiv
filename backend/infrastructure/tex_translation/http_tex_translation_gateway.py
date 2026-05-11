import os
from logging import getLogger

import httpx

from domain.errors import (
	ArxivPaperNotFoundError,
	LatexCompilationTimeoutError,
	TexFileNotFoundError,
	TranslationFailedError,
)
from domain.gateways import ITexTranslationGateway
from domain.value_objects import ArxivPaperId, TargetLanguage
from infrastructure.tex_translation.config import get_tex_translation_config


class HttpTexTranslationGateway(ITexTranslationGateway):
	"""Gateway implementation that delegates to the tex_translation microservice."""

	def __init__(self) -> None:
		self._logger = getLogger(__name__)
		config = get_tex_translation_config()
		self._base_url = config.tex_translation_url.rstrip('/')
		self._timeout = config.tex_translation_timeout_seconds

	async def translate_to_pdf(
		self,
		arxiv_paper_id: ArxivPaperId,
		target_language: TargetLanguage,
		output_dir: str,
	) -> str:
		url = f'{self._base_url}/api/v1/translate/arxiv/{arxiv_paper_id.root}'
		params = {'target_language': target_language.value}

		self._logger.info(
			'Calling tex_translation service: POST %s (timeout=%ss)', url, self._timeout
		)
		try:
			async with httpx.AsyncClient(timeout=self._timeout) as client:
				response = await client.post(url, params=params)
		except httpx.TimeoutException as e:
			raise LatexCompilationTimeoutError(arxiv_paper_id.root) from e
		except httpx.HTTPError as e:
			raise TranslationFailedError(f'tex_translation request failed: {e}') from e

		if response.status_code == 404:
			detail = self._extract_detail(response)
			if 'No tex file found' in detail:
				raise TexFileNotFoundError(arxiv_paper_id.root, detail=detail)
			raise ArxivPaperNotFoundError(arxiv_paper_id.root)
		if response.status_code == 504:
			raise LatexCompilationTimeoutError(arxiv_paper_id.root)
		if response.status_code >= 400:
			raise TranslationFailedError(
				f'tex_translation returned {response.status_code}: '
				f'{self._extract_detail(response)}'
			)

		# Write into a per-paper subdirectory so the caller can safely rmtree the
		# parent once the PDF has been uploaded to long-term storage.
		paper_dir = os.path.join(output_dir, arxiv_paper_id.root)
		os.makedirs(paper_dir, exist_ok=True)
		pdf_path = os.path.join(paper_dir, f'{arxiv_paper_id.root}_translated.pdf')
		with open(pdf_path, 'wb') as f:
			f.write(response.content)
		self._logger.info('Saved translated PDF to %s', pdf_path)
		return pdf_path

	@staticmethod
	def _extract_detail(response: httpx.Response) -> str:
		try:
			body = response.json()
		except ValueError:
			return response.text
		if isinstance(body, dict) and 'detail' in body:
			return str(body['detail'])
		return response.text
