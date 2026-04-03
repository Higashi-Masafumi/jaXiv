from functools import lru_cache

from fastapi import Depends
from onnxruntime import InferenceSession
from transformers import AutoImageProcessor, AutoModel, AutoTokenizer

from domain.gateways.figure_extractor import FigureExtractorGateway
from domain.gateways.image_embedding import ImageEmbeddingGateway
from domain.gateways.pdf_chunker import PdfChunkerGateway
from domain.gateways.text_embedding import TextEmbeddingGateway
from infrastructure.bge.text_embedding import BgeTextEmbeddingGateway
from infrastructure.nomic.image_embedding import NomicImageEmbeddingGateway
from infrastructure.nomic.text_embedding import NomicTextEmbeddingGateway
from infrastructure.onnx.model_loader import load_onnx_session
from infrastructure.onnx.pdf_figure_extractor import PdfFigureExtractor
from infrastructure.pdf_parse import PyMuPdfChunker
from usecase.chunk_and_embed import ChunkAndEmbedUseCase
from usecase.extract_figures import ExtractFiguresUseCase
from usecase.extract_figures_with_embeddings import ExtractFiguresWithEmbeddingsUseCase

NOMIC_VISION_MODEL = "nomic-ai/nomic-embed-vision-v1.5"
NOMIC_TEXT_MODEL = "nomic-ai/nomic-embed-text-v1.5"
BGE_TEXT_MODEL = "BAAI/bge-base-en-v1.5"


@lru_cache
def get_onnx_session() -> InferenceSession:
    return load_onnx_session()


@lru_cache
def get_nomic_image_embedding_gateway() -> NomicImageEmbeddingGateway:
    # local_files_only=True: HF hub が再ダウンロードして n_inner=2048.0(float) に戻るのを防ぐ
    processor = AutoImageProcessor.from_pretrained(NOMIC_VISION_MODEL)
    model = AutoModel.from_pretrained(NOMIC_VISION_MODEL, trust_remote_code=True)
    return NomicImageEmbeddingGateway(model=model, processor=processor)


@lru_cache
def get_nomic_text_embedding_gateway() -> NomicTextEmbeddingGateway:
    tokenizer = AutoTokenizer.from_pretrained(NOMIC_TEXT_MODEL, trust_remote_code=True)
    model = AutoModel.from_pretrained(NOMIC_TEXT_MODEL, trust_remote_code=True)
    return NomicTextEmbeddingGateway(model=model, tokenizer=tokenizer)


@lru_cache
def get_bge_text_embedding_gateway() -> BgeTextEmbeddingGateway:
    tokenizer = AutoTokenizer.from_pretrained(BGE_TEXT_MODEL)
    model = AutoModel.from_pretrained(BGE_TEXT_MODEL)
    return BgeTextEmbeddingGateway(model=model, tokenizer=tokenizer)


def get_extractor(
    session: InferenceSession = Depends(get_onnx_session),
) -> FigureExtractorGateway:
    return PdfFigureExtractor(session=session)


def get_pdf_chunker() -> PdfChunkerGateway:
    return PyMuPdfChunker()


def get_extract_figures_use_case(
    extractor: FigureExtractorGateway = Depends(get_extractor),
) -> ExtractFiguresUseCase:
    return ExtractFiguresUseCase(extractor=extractor)


def get_extract_figures_with_embeddings_use_case(
    extractor: FigureExtractorGateway = Depends(get_extractor),
    image_embedding: ImageEmbeddingGateway = Depends(get_nomic_image_embedding_gateway),
    caption_embedding: TextEmbeddingGateway = Depends(get_nomic_text_embedding_gateway),
) -> ExtractFiguresWithEmbeddingsUseCase:
    return ExtractFiguresWithEmbeddingsUseCase(
        extractor=extractor,
        image_embedding=image_embedding,
        caption_embedding=caption_embedding,
    )


def get_chunk_and_embed_use_case(
    chunker: PdfChunkerGateway = Depends(get_pdf_chunker),
    text_embedding: TextEmbeddingGateway = Depends(get_bge_text_embedding_gateway),
) -> ChunkAndEmbedUseCase:
    return ChunkAndEmbedUseCase(chunker=chunker, text_embedding=text_embedding)
