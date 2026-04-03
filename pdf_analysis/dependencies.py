from functools import lru_cache

from fastapi import Depends
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from onnxruntime import InferenceSession

from domain.gateways.embedding import EmbeddingGateway
from domain.gateways.figure_extractor import FigureExtractorGateway
from domain.gateways.pdf_chunker import PdfChunkerGateway
from infrastructure.huggingface.embedding import HuggingFaceEmbeddingGateway
from infrastructure.onnx.model_loader import load_onnx_session
from infrastructure.onnx.pdf_figure_extractor import PdfFigureExtractor
from infrastructure.pdf_parse import PyMuPdfChunker
from usecase.chunk_and_embed import ChunkAndEmbedUseCase
from usecase.extract_figures import ExtractFiguresUseCase
from usecase.extract_figures_with_embeddings import ExtractFiguresWithEmbeddingsUseCase


@lru_cache
def get_onnx_session() -> InferenceSession:
    return load_onnx_session()


@lru_cache
def get_figure_embedding_model() -> HuggingFaceEmbedding:
    # VDR は ST の max_seq_length が None になり得るが、HuggingFaceEmbedding は int 必須（llama-index 実装）
    return HuggingFaceEmbedding(
        model_name="llamaindex/vdr-2b-multi-v1",
        device="cpu",
        trust_remote_code=True,
        max_length=32768,
    )


@lru_cache
def get_text_embedding_model() -> HuggingFaceEmbedding:
    return HuggingFaceEmbedding(model_name="BAAI/bge-base-en-v1.5", device="cpu")


def get_extractor(
    session: InferenceSession = Depends(get_onnx_session),
) -> FigureExtractorGateway:
    return PdfFigureExtractor(session=session)


def get_figure_embedding_gateway(
    model: HuggingFaceEmbedding = Depends(get_figure_embedding_model),
) -> EmbeddingGateway:
    return HuggingFaceEmbeddingGateway(model=model)


def get_text_embedding_gateway(
    model: HuggingFaceEmbedding = Depends(get_text_embedding_model),
) -> EmbeddingGateway:
    return HuggingFaceEmbeddingGateway(model=model)


def get_pdf_chunker() -> PdfChunkerGateway:
    return PyMuPdfChunker()


def get_extract_figures_use_case(
    extractor: FigureExtractorGateway = Depends(get_extractor),
) -> ExtractFiguresUseCase:
    return ExtractFiguresUseCase(extractor=extractor)


def get_extract_figures_with_embeddings_use_case(
    extractor: FigureExtractorGateway = Depends(get_extractor),
    embedding: EmbeddingGateway = Depends(get_figure_embedding_gateway),
) -> ExtractFiguresWithEmbeddingsUseCase:
    return ExtractFiguresWithEmbeddingsUseCase(extractor=extractor, embedding=embedding)


def get_chunk_and_embed_use_case(
    chunker: PdfChunkerGateway = Depends(get_pdf_chunker),
    embedding: EmbeddingGateway = Depends(get_text_embedding_gateway),
) -> ChunkAndEmbedUseCase:
    return ChunkAndEmbedUseCase(chunker=chunker, embedding=embedding)
