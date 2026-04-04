"""Download PDF by HTTPS URL with size limits."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import httpx


@contextmanager
def pdf_temp_path_from_url(url: str) -> Iterator[Path]:
    """Stream-download a PDF to a temp file; delete the file on exit.

    ``url`` must already be validated (e.g. ``PdfUrlRequest.pdf_url``).
    """
    fd, name = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    path = Path(name)
    try:
        with httpx.Client(
            timeout=httpx.Timeout(300.0), follow_redirects=True
        ) as client:
            with client.stream("GET", url) as response:
                response.raise_for_status()
                with path.open("wb") as f:
                    for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                        f.write(chunk)
        yield path
    finally:
        path.unlink(missing_ok=True)
