import logging

import sentry_sdk
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.logging import LoggingIntegration

from controller import router

load_dotenv()

logging.basicConfig(
	level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(title='Translate Arxiv Paper', version='0.1.0')
app.include_router(router)

app.add_middleware(
	CORSMiddleware,
	allow_origins=['*'],
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
