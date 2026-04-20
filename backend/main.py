import logging
from contextlib import asynccontextmanager
from typing import Any

import sentry_sdk
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pydantic import TypeAdapter
from sentry_sdk.integrations.logging import LoggingIntegration

from application.chat_events import ChatStreamEvent
from controller import router
from infrastructure.qdrant import QdrantFigureChunkRepository, QdrantTextChunkRepository

load_dotenv()

logging.basicConfig(
	level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@asynccontextmanager
async def lifespan(app: FastAPI):
	QdrantTextChunkRepository().ensure_collection()
	QdrantFigureChunkRepository().ensure_collection()
	yield


app = FastAPI(title='Translate Arxiv Paper', version='0.1.0', lifespan=lifespan)
app.include_router(router)


def _rewrite_refs(obj: Any, old_prefix: str, new_prefix: str) -> Any:
    """Recursively rewrite JSON Schema $ref paths and discriminator mappings."""
    if isinstance(obj, dict):
        result: dict[str, Any] = {}
        for k, v in obj.items():
            if k == '$ref' and isinstance(v, str):
                result[k] = v.replace(old_prefix, new_prefix)
            elif k == 'mapping' and isinstance(v, dict):
                # discriminator.mapping values are also refs
                result[k] = {
                    mk: mv.replace(old_prefix, new_prefix) if isinstance(mv, str) else mv
                    for mk, mv in v.items()
                }
            else:
                result[k] = _rewrite_refs(v, old_prefix, new_prefix)
        return result
    if isinstance(obj, list):
        return [_rewrite_refs(v, old_prefix, new_prefix) for v in obj]
    return obj


def custom_openapi() -> dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    # Inject chat stream event schemas so hey-api can generate TypeScript types
    adapter: TypeAdapter[ChatStreamEvent] = TypeAdapter(ChatStreamEvent)
    event_schemas = adapter.json_schema(mode='serialization')
    defs = event_schemas.pop('$defs', {})
    # Rewrite internal $refs from #/$defs/X → #/components/schemas/X
    event_schemas = _rewrite_refs(event_schemas, '#/$defs/', '#/components/schemas/')
    defs = _rewrite_refs(defs, '#/$defs/', '#/components/schemas/')
    schema.setdefault('components', {}).setdefault('schemas', {}).update(defs)
    schema['components']['schemas']['ChatStreamEvent'] = event_schemas
    # Annotate the SSE endpoint response with the ChatStreamEvent schema
    for path_item in schema.get('paths', {}).values():
        for op in path_item.values():
            if isinstance(op, dict) and 'text/event-stream' in str(
                op.get('responses', {})
            ):
                op.setdefault('responses', {}).setdefault('200', {}).setdefault(
                    'content', {}
                )['text/event-stream'] = {
                    'schema': {'$ref': '#/components/schemas/ChatStreamEvent'}
                }
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi  # type: ignore[method-assign]

app.add_middleware(
	CORSMiddleware,
	allow_origins=['*', 'http://localhost:5173'],
	allow_credentials=True,
	allow_methods=['*'],
	allow_headers=['*'],
)

sentry_sdk.init(
	dsn='https://382d77a1d801f0362e4c2fb9644c6bdc@o4509661921083392.ingest.us.sentry.io/4509661921935360',
	integrations=[
		LoggingIntegration(
			level=logging.INFO,  # Capture info and above as breadcrumbs
			event_level=logging.WARNING,  # Send errors as events
		),
	],
	send_default_pii=True,
)


@app.get('/')
async def root():
	return {'message': 'Hello World'}


@app.get('/sentry-debug')
async def trigger_error():
	1 / 0
