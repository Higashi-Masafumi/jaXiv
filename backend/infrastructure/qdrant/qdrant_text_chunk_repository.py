import uuid
from typing import cast

from qdrant_client import QdrantClient
from qdrant_client.models import (
	Distance,
	FieldCondition,
	Filter,
	MatchValue,
	PayloadSchemaType,
	PointStruct,
	VectorParams,
)

from domain.entities.document_chunk import DocumentTextChunk
from domain.repositories.i_text_chunk_repository import ITextChunkRepository
from domain.value_objects.arxiv_paper_id import ArxivPaperId
from domain.value_objects.embedding import Embedding
from domain.value_objects.pdf_paper_id import PdfPaperId

from infrastructure.qdrant.config import get_qdrant_config

qdrant_config = get_qdrant_config()


class QdrantTextChunkRepository(ITextChunkRepository):
	"""Qdrant implementation for text chunks using a single dense vector (BGE)."""

	VECTOR_DIM = 768

	def __init__(self) -> None:
		self._client = QdrantClient(
			url=qdrant_config.qdrant_url.get_secret_value(),
			api_key=qdrant_config.qdrant_api_key.get_secret_value(),
		)

	def ensure_collection(self) -> None:
		existing = {c.name for c in self._client.get_collections().collections}
		if qdrant_config.text_collection_name not in existing:
			self._client.create_collection(
				collection_name=qdrant_config.text_collection_name,
				vectors_config=VectorParams(size=self.VECTOR_DIM, distance=Distance.COSINE),
			)
		self._client.create_payload_index(
			collection_name=qdrant_config.text_collection_name,
			field_name='paper_id',
			field_schema=PayloadSchemaType.KEYWORD,
		)

	async def save(self, chunk: DocumentTextChunk) -> None:
		self._client.upsert(
			collection_name=qdrant_config.text_collection_name,
			points=[
				PointStruct(
					id=str(uuid.uuid4()),
					vector=chunk.embeddings.root,
					payload={
						'paper_id': chunk.paper_id.root,
						'text': chunk.text,
						'page_number': chunk.page_number,
						'chunk_type': chunk.chunk_type,
					},
				)
			],
		)

	async def query(
		self,
		paper_id: ArxivPaperId | PdfPaperId,
		query_embeddings: Embedding,
		limit: int = 5,
	) -> list[DocumentTextChunk]:
		response = self._client.query_points(
			collection_name=qdrant_config.text_collection_name,
			query=query_embeddings.root,
			query_filter=Filter(
				must=[FieldCondition(key='paper_id', match=MatchValue(value=paper_id.root))]
			),
			limit=limit,
			with_payload=True,
			with_vectors=True,
		)
		out: list[DocumentTextChunk] = []
		for point in response.points:
			if point.payload is None or point.vector is None:
				continue
			vec = point.vector
			if isinstance(vec, dict):
				continue
			out.append(
				DocumentTextChunk(
					chunk_type='text',
					paper_id=paper_id,
					text=point.payload['text'],
					page_number=point.payload['page_number'],
					embeddings=Embedding(cast(list[float], vec)),
				)
			)
		return out
