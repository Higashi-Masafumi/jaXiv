from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from controller.extract import router
from infrastructure.onnx.model_loader import load_onnx_session
from infrastructure.onnx.pdf_figure_extractor import PdfFigureExtractor
from usecase.extract_figures import ExtractFiguresUseCase


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    session = load_onnx_session()
    extractor = PdfFigureExtractor(session=session)
    app.state.extract_figures_use_case = ExtractFiguresUseCase(extractor=extractor)
    yield


app = FastAPI(title="Layout Analysis Service", version="0.1.0", lifespan=lifespan)
app.include_router(router)
