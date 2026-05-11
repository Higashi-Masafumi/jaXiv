from abc import ABC, abstractmethod

from domain.value_objects import ArxivPaperId, TargetLanguage


class ITexTranslationGateway(ABC):
	"""Gateway to the external TeX translation microservice.

	The remote service downloads the arXiv source, translates each ``.tex`` file
	with an LLM, compiles the result via ``latexmk``, and returns the produced
	PDF as binary bytes.
	"""

	@abstractmethod
	async def translate_to_pdf(
		self,
		arxiv_paper_id: ArxivPaperId,
		target_language: TargetLanguage,
	) -> bytes:
		"""Translate ``arxiv_paper_id`` and return the compiled PDF as bytes.

		Raises:
		    ArxivPaperNotFoundError: If the remote service reports 404.
		    TexFileNotFoundError: If the remote service reports the tex source is missing.
		    TranslationFailedError: For any other remote failure.
		    LatexCompilationTimeoutError: If the remote service timed out compiling.
		"""
