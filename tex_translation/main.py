import logging

from dotenv import load_dotenv
from fastapi import FastAPI

from controller import router
from middlewares import ExceptionHandler

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Tex Translation Service",
    version="0.1.0",
    description=(
        "Fetches arXiv LaTeX source, translates each .tex file via an LLM, "
        "then compiles to PDF with TeX Live."
    ),
)
app.include_router(router)
app.add_middleware(ExceptionHandler)

logger.info("Tex Translation Service started.")
