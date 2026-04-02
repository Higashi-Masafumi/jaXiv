import logging

from fastapi import FastAPI

from controller.extract import router

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Layout Analysis Service", version="0.1.0")
app.include_router(router)

logger.debug("Layout Analysis Service application started successfully.")
