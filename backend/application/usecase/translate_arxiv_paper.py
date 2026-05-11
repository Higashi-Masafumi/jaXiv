from collections.abc import AsyncGenerator
from logging import getLogger

from domain.entities import (
	CompleteTranslateChunk,
	ErrorTranslateChunk,
	IntermediateTranslateChunk,
	TypedTranslateChunk,
)
from domain.errors import TranslationFailedError
from domain.gateways import ITexTranslationGateway
from domain.value_objects import ArxivPaperId, TargetLanguage


class TranslateArxivPaper:
	"""Translate an arXiv paper by delegating to the tex_translation microservice."""

	def __init__(self, tex_translation_gateway: ITexTranslationGateway):
		self._logger = getLogger(__name__)
		self._tex_translation_gateway = tex_translation_gateway

	async def execute(
		self,
		arxiv_paper_id: ArxivPaperId,
		target_language: TargetLanguage,
		output_dir: str,
	) -> AsyncGenerator[TypedTranslateChunk]:
		"""
		Yields a coarse progress stream around the external service call:

		- start (0%)
		- delegating to remote service (10%)
		- completed (100%) with the local path to the downloaded PDF

		Fine-grained progress is owned by the remote service; this use case keeps
		the streaming contract that the controllers expect.
		"""
		self._logger.info(
			'Translating %s to %s via tex_translation service',
			arxiv_paper_id.root,
			target_language,
		)
		yield IntermediateTranslateChunk(
			message=f'Translating Arxiv {arxiv_paper_id.root} to {target_language}',
			progress_percentage=0,
		)

		yield IntermediateTranslateChunk(
			message=f'Delegating compile+translate of Arxiv {arxiv_paper_id.root} to tex service',
			progress_percentage=10,
		)

		try:
			pdf_path = await self._tex_translation_gateway.translate_to_pdf(
				arxiv_paper_id=arxiv_paper_id,
				target_language=target_language,
				output_dir=output_dir,
			)
		except TranslationFailedError as e:
			yield ErrorTranslateChunk(
				message=f'Failed to translate Arxiv {arxiv_paper_id.root}',
				progress_percentage=10,
				error_details=str(e),
			)
			raise
		except Exception as e:
			self._logger.exception('Error translating %s', arxiv_paper_id.root)
			yield ErrorTranslateChunk(
				message=f'Error translating Arxiv {arxiv_paper_id.root}',
				progress_percentage=10,
				error_details=str(e),
			)
			raise

		yield CompleteTranslateChunk(
			message=f'Translated Arxiv {arxiv_paper_id.root}',
			progress_percentage=100,
			translated_pdf_path=pdf_path,
		)
