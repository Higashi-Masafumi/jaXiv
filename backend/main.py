from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controller.translate import router
import logging
from dotenv import load_dotenv
import sentry_sdk
import os

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(title="Translate Arxiv Paper", version="0.1.0")
app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sentry_sdk.init(
    dsn="https://382d77a1d801f0362e4c2fb9644c6bdc@o4509661921083392.ingest.us.sentry.io/4509661921935360",
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0