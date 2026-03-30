from fastapi import FastAPI

from controller.extract import router

app = FastAPI(title="Layout Analysis Service", version="0.1.0")
app.include_router(router)
