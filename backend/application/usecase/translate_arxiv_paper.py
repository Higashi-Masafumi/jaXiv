from logging import getLogger

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
	) -> bytes:
		"""Return the translated PDF bytes produced by the remote service."""
		self._logger.info(
			'Translating %s to %s via tex_translation service',
			arxiv_paper_id.root,
			target_language,
		)
		return await self._tex_translation_gateway.translate_to_pdf(
			arxiv_paper_id=arxiv_paper_id,
			target_language=target_language,
		)
