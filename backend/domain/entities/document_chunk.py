from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, StrictStr

from domain.value_objects.arxiv_paper_id import ArxivPaperId
from domain.value_objects.embedding import Embedding
from domain.value_objects.image_url import ImageUrl
from domain.value_objects.pdf_paper_id import PdfPaperId


class DocumentTextChunk(BaseModel):
	model_config = ConfigDict(frozen=True)
	chunk_type: Literal['text']
	paper_id: ArxivPaperId | PdfPaperId
	text: StrictStr
	page_number: int
	embeddings: Embedding


class DocumentFigureChunk(BaseModel):
	model_config = ConfigDict(frozen=True)
	chunk_type: Literal['figure']
	paper_id: ArxivPaperId | PdfPaperId
	image_url: ImageUrl
	caption: StrictStr | None
	page_number: int
	embeddings: Embedding


DocumentChunk = Annotated[
	Union[DocumentTextChunk, DocumentFigureChunk], Field(discriminator='chunk_type')
]
