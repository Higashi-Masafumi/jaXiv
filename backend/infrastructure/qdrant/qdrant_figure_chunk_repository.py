import uuid
from typing import Literal, cast

from qdrant_client import QdrantClient
from qdrant_client.models import (
	Distance,
	FieldCondition,
	Filter,
	MatchValue,
	PointStruct,
	VectorParams,
)

from domain.entities.document_chunk import DocumentFigureChunk
from domain.repositories.i_figure_chunk_repository import IFigureChunkRepository
from domain.value_objects.arxiv_paper_id import ArxivPaperId
from domain.value_objects.embedding import Embedding
from domain.value_objects.image_url import ImageUrl
from domain.value_objects.pdf_paper_id import PdfPaperId


class QdrantFigureChunkRepository(IFigureChunkRepository):
	"""Qdrant implementation of IFigureChunkRepository.

	Stores each figure as a single Qdrant point with named vectors:
	  - "image": image embedding from vdr-2b-multi-v1
	  - "caption": caption embedding from vdr-2b-multi-v1
	"""

	COLLECTION_NAME = 'figures'
	# llamaindex/vdr-2b-multi-v1 output dimension
	IMAGE_DIM = 2048
	CAPTION_DIM = 2048

	def __init__(self, client: QdrantClient) -> None:
		self._client = client
		self._ensure_collection()

	def _ensure_collection(self) -> None:
		existing = {c.name for c in self._client.get_collections().collections}
		if self.COLLECTION_NAME not in existing:
			self._client.create_collection(
				collection_name=self.COLLECTION_NAME,
				vectors_config={
					'image': VectorParams(size=self.IMAGE_DIM, distance=Distance.COSINE),
					'caption': VectorParams(size=self.CAPTION_DIM, distance=Distance.COSINE),
				},
			)

	async def save(self, chunk: DocumentFigureChunk) -> None:
		self._client.upsert(
			collection_name=self.COLLECTION_NAME,
			points=[
				PointStruct(
					id=str(uuid.uuid4()),
					vector={
						'image': chunk.image_embeddings.root,
						'caption': chunk.caption_embeddings.root,
					},
					payload={
						'paper_id': chunk.paper_id.root,
						'image_url': str(chunk.image_url.root),
						'caption': chunk.caption,
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
		using: Literal['image', 'caption'] = 'caption',
		limit: int = 5,
	) -> list[DocumentFigureChunk]:
		response = self._client.query_points(
			collection_name=self.COLLECTION_NAME,
			query=query_embeddings.root,
			using=using,
			query_filter=Filter(
				must=[FieldCondition(key='paper_id', match=MatchValue(value=paper_id.root))]
			),
			limit=limit,
			with_payload=True,
			with_vectors=True,
		)
		out: list[DocumentFigureChunk] = []
		for point in response.points:
			if point.payload is None or point.vector is None:
				continue
			vecs = point.vector
			if not isinstance(vecs, dict):
				continue
			out.append(
				DocumentFigureChunk(
					chunk_type='figure',
					paper_id=paper_id,
					image_url=ImageUrl(url=point.payload['image_url']),
					caption=point.payload['caption'],
					page_number=point.payload['page_number'],
					image_embeddings=Embedding(cast(list[float], vecs['image'])),
					caption_embeddings=Embedding(cast(list[float], vecs['caption'])),
				)
			)
		return out
