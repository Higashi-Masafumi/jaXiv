import uuid
from typing import cast

from qdrant_client import QdrantClient
from qdrant_client.models import (
	Distance,
	FieldCondition,
	Filter,
	Fusion,
	FusionQuery,
	MatchValue,
	PayloadSchemaType,
	PointStruct,
	Prefetch,
	ScoredPoint,
	VectorParams,
)

from domain.entities.document_chunk import DocumentFigureChunk
from domain.repositories.i_figure_chunk_repository import (
	FigureSearchMode,
	GlobalFigureHit,
	IFigureChunkRepository,
)
from domain.value_objects.arxiv_paper_id import ArxivPaperId
from domain.value_objects.embedding import Embedding
from domain.value_objects.image_url import ImageUrl
from domain.value_objects.pdf_paper_id import PdfPaperId

from infrastructure.qdrant.config import get_qdrant_config

qdrant_config = get_qdrant_config()


class QdrantFigureChunkRepository(IFigureChunkRepository):
	"""Qdrant implementation of IFigureChunkRepository.

	Stores each figure as a single Qdrant point with named vectors:
	  - "image": image embedding from nomic-embed-vision-v1.5
	  - "caption": caption embedding from nomic-embed-text-v1.5
	"""

	# nomic-ai/nomic-embed-vision-v1.5 and nomic-ai/nomic-embed-text-v1.5 output dimension
	IMAGE_DIM = 768
	CAPTION_DIM = 768

	def __init__(self) -> None:
		self._client = QdrantClient(
			url=qdrant_config.qdrant_url.get_secret_value(),
			api_key=qdrant_config.qdrant_api_key.get_secret_value(),
		)

	def ensure_collection(self) -> None:
		existing = {c.name for c in self._client.get_collections().collections}
		if qdrant_config.figure_collection_name not in existing:
			self._client.create_collection(
				collection_name=qdrant_config.figure_collection_name,
				vectors_config={
					'image': VectorParams(size=self.IMAGE_DIM, distance=Distance.COSINE),
					'caption': VectorParams(size=self.CAPTION_DIM, distance=Distance.COSINE),
				},
			)
		self._client.create_payload_index(
			collection_name=qdrant_config.figure_collection_name,
			field_name='paper_id',
			field_schema=PayloadSchemaType.KEYWORD,
		)

	async def save(self, chunk: DocumentFigureChunk) -> None:
		self._client.upsert(
			collection_name=qdrant_config.figure_collection_name,
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

	def _search(
		self,
		query_embeddings: Embedding,
		mode: FigureSearchMode,
		limit: int,
		with_vectors: bool,
		query_filter: Filter | None = None,
	) -> list[ScoredPoint]:
		"""Run a figure similarity search in the requested mode.

		``image``/``caption`` score against a single named vector. ``hybrid``
		prefetches both and fuses the two rankings with reciprocal rank fusion
		(RRF), which is robust to the differing score scales of the two vectors.
		"""
		if mode == 'hybrid':
			response = self._client.query_points(
				collection_name=qdrant_config.figure_collection_name,
				prefetch=[
					Prefetch(
						query=query_embeddings.root,
						using='image',
						filter=query_filter,
						limit=limit,
					),
					Prefetch(
						query=query_embeddings.root,
						using='caption',
						filter=query_filter,
						limit=limit,
					),
				],
				query=FusionQuery(fusion=Fusion.RRF),
				limit=limit,
				with_payload=True,
				with_vectors=with_vectors,
			)
		else:
			response = self._client.query_points(
				collection_name=qdrant_config.figure_collection_name,
				query=query_embeddings.root,
				using=mode,
				query_filter=query_filter,
				limit=limit,
				with_payload=True,
				with_vectors=with_vectors,
			)
		return response.points

	async def query(
		self,
		paper_id: ArxivPaperId | PdfPaperId,
		query_embeddings: Embedding,
		mode: FigureSearchMode = 'hybrid',
		limit: int = 5,
	) -> list[DocumentFigureChunk]:
		points = self._search(
			query_embeddings,
			mode,
			limit,
			with_vectors=True,
			query_filter=Filter(
				must=[FieldCondition(key='paper_id', match=MatchValue(value=paper_id.root))]
			),
		)
		out: list[DocumentFigureChunk] = []
		for point in points:
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

	async def query_global(
		self,
		query_embeddings: Embedding,
		mode: FigureSearchMode = 'hybrid',
		limit: int = 20,
	) -> list[GlobalFigureHit]:
		# No paper_id filter: search figures across every paper.
		points = self._search(query_embeddings, mode, limit, with_vectors=False)
		out: list[GlobalFigureHit] = []
		for point in points:
			if point.payload is None:
				continue
			out.append(
				GlobalFigureHit(
					paper_id=point.payload['paper_id'],
					image_url=point.payload['image_url'],
					caption=point.payload.get('caption'),
					page_number=point.payload['page_number'],
					score=point.score,
				)
			)
		return out
