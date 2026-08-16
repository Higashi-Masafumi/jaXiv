"""Memory-bounded helpers for talking to the pdf_analysis service.

The service answers with a single JSON document that embeds every extracted
figure as base64, so a paper with 20 figures easily produces tens of megabytes.
Reading that with ``response.json()`` costs several copies of the whole document
at once — the buffered body, the ``str`` the stdlib parser decodes it into, the
parsed structure, and finally every decoded image — which is what pushes the
512MB container over its limit. The helpers here spool the body to disk and then
walk it item by item, so peak memory tracks a single figure instead of a paper.
"""

import base64
import tempfile
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import Any

import httpx
import ijson

from domain.errors.domain_error import PdfProcessingError
from libs import AsyncClient


@contextmanager
def pdf_upload_file(pdf_path: Path) -> Iterator[dict[str, tuple[str, Any, str]]]:
	"""Yield an httpx ``files=`` mapping that streams ``pdf_path`` from disk.

	Passing ``pdf_path.read_bytes()`` instead would hold the whole PDF in memory
	on top of the multipart body httpx builds from it.
	"""
	with pdf_path.open('rb') as pdf_file:
		yield {'file': (pdf_path.name, pdf_file, 'application/pdf')}


@asynccontextmanager
async def post_json_items(
	client: AsyncClient, path: str, service: str, item_prefix: str, **kwargs: Any
) -> AsyncIterator[Iterator[dict]]:
	"""POST to the pdf_analysis service and yield the response items one by one.

	The body is spooled to a temporary file and then parsed incrementally, so
	neither the raw bytes nor the whole parsed document is ever resident. Only the
	item currently being consumed is in memory.

	Args:
	    item_prefix: ijson prefix of the array to walk, e.g. ``'figures.item'``.
	"""
	with tempfile.NamedTemporaryFile(suffix='.json') as body_file:
		try:
			response = await client.post_to_file(path, dest=body_file, **kwargs)
		except (httpx.ConnectError, httpx.TimeoutException) as e:
			raise PdfProcessingError(f'{service} service error: {e}') from e
		if response.status_code != 200:
			raise PdfProcessingError(
				f'{service} service returned {response.status_code}: {response.text}'
			)
		# use_float: 既定の Decimal は 768 次元の埋め込みでは重すぎるため float で受ける。
		yield ijson.items(body_file, item_prefix, use_float=True)


def write_figure_image(item: dict, image_dir: Path, index: int) -> Path:
	"""Move a figure's base64 payload out of ``item`` and onto disk, returning its path.

	The base64 string is popped from the payload so that both it and the decoded
	bytes become garbage as soon as the file is written: only one figure is ever
	resident in memory, instead of every figure of the paper at once.
	"""
	image_path = image_dir / f'figure_{index}.png'
	image_path.write_bytes(base64.b64decode(item.pop('image_base64')))
	return image_path
