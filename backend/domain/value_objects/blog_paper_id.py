"""Blog / RAG 用の論文 ID。arXiv 形式と PDF アップロード由来の ID の和を型で表す。"""

from pydantic import ConfigDict, RootModel

from domain.errors import DomainError
from domain.value_objects.arxiv_paper_id import ArxivPaperId, InvalidArxivPaperIdError
from domain.value_objects.pdf_paper_id import PdfPaperId, InvalidPdfPaperIdError


class InvalidBlogPaperIdError(DomainError):
	"""パス上の文字列がどちらの論文 ID 形式にも合わないとき。"""


class BlogPaperId(RootModel[ArxivPaperId | PdfPaperId]):
	"""`ArxivPaperId` と `PdfPaperId` の判別和を値オブジェクトとして包む。"""

	model_config = ConfigDict(frozen=True)

	@classmethod
	def from_raw(cls, raw: str) -> 'BlogPaperId':
		s = raw.strip()
		if s.startswith('pdf-'):
			try:
				return cls(PdfPaperId(s))
			except InvalidPdfPaperIdError as e:
				raise InvalidBlogPaperIdError(str(e)) from e
		try:
			return cls(ArxivPaperId(s))
		except InvalidArxivPaperIdError as e:
			raise InvalidBlogPaperIdError(str(e)) from e
