from functools import lru_cache

from fastapi import Depends
from onnxruntime import InferenceSession

from domain.gateways.figure_extractor import FigureExtractorGateway
from infrastructure.onnx.model_loader import load_onnx_session
from infrastructure.onnx.pdf_figure_extractor import PdfFigureExtractor
from usecase.extract_figures import ExtractFiguresUseCase


@lru_cache
def get_onnx_session() -> InferenceSession:
    return load_onnx_session()


def get_extractor(
    session: InferenceSession = Depends(get_onnx_session),
) -> FigureExtractorGateway:
    return PdfFigureExtractor(session=session)


def get_extract_figures_use_case(
    extractor: FigureExtractorGateway = Depends(get_extractor),
) -> ExtractFiguresUseCase:
    return ExtractFiguresUseCase(extractor=extractor)
