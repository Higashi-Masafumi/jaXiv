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


class QdrantTextChunkRepository(ITextChunkRepository):
	"""Qdrant implementation for text chunks using a single dense vector (BGE)."""

	COLLECTION_NAME = 'text_chunks'
	VECTOR_DIM = 768

	def __init__(self, client: QdrantClient) -> None:
		self._client = client
		self._ensure_collection()

	def _ensure_collection(self) -> None:
		existing = {c.name for c in self._client.get_collections().collections}
		if self.COLLECTION_NAME not in existing:
			self._client.create_collection(
				collection_name=self.COLLECTION_NAME,
				vectors_config=VectorParams(size=self.VECTOR_DIM, distance=Distance.COSINE),
			)
		self._client.create_payload_index(
			collection_name=self.COLLECTION_NAME,
			field_name='paper_id',
			field_schema=PayloadSchemaType.KEYWORD,
		)

	async def save(self, chunk: DocumentTextChunk) -> None:
		self._client.upsert(
			collection_name=self.COLLECTION_NAME,
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
			collection_name=self.COLLECTION_NAME,
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
