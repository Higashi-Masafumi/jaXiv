import logging

from fastapi import FastAPI

from controller.extract import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# uvicorn --host 0.0.0.0 だと OpenAPI の servers が http://0.0.0.0:... になり、
# Swagger UI の Try it out がブラウザで不正な URL になり「URL scheme must be http or https」等になる。
# 相対 URL にして、閲覧中のホスト（localhost:7860 等）に向ける。
app = FastAPI(
    title="Layout Analysis Service",
    version="0.1.0",
    servers=[{"url": "/", "description": "Current origin"}],
)
app.include_router(router)

logger.info("Layout Analysis Service application started successfully.")
