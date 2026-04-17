import mimetypes
import tempfile
from logging import getLogger
from pathlib import Path
from typing import ClassVar

from pdf2image import convert_from_path
from supabase import create_async_client

from domain.repositories import IFigureStorageRepository

from infrastructure.supabase.config import get_supabase_config

supabase_config = get_supabase_config()


class SupabaseFigureStorageRepository(IFigureStorageRepository):
	"""Uploads figures from a LaTeX source directory to Supabase Storage."""

	FIGURE_EXTENSIONS: ClassVar[set[str]] = {
		'.png',
		'.jpg',
		'.jpeg',
		'.gif',
		'.webp',
		'.svg',
		'.eps',
		'.pdf',
	}

	def __init__(self):
		self._supabase_url = supabase_config.supabase_url.get_secret_value()
		self._supabase_key = supabase_config.supabase_api_key.get_secret_value()
		self._bucket_name = supabase_config.blog_figures_bucket_name
		self._logger = getLogger(__name__)

	async def upload_figures(self, paper_id: str, source_dir: Path) -> dict[str, str]:
		"""
		Upload all figure files from source_dir to Supabase Storage.

		Args:
		    paper_id: The arXiv paper ID (used as a path prefix).
		    source_dir: Path to the extracted LaTeX source directory.

		Returns:
		    A dict mapping each figure's filename to its public URL.
		"""
		figure_files = [
			f for f in source_dir.rglob('*') if f.suffix.lower() in self.FIGURE_EXTENSIONS
		]
		if not figure_files:
			self._logger.info('No figure files found in %s', source_dir)
			return {}

		self._logger.info('Uploading %d figures for paper %s', len(figure_files), paper_id)
		supabase = await create_async_client(self._supabase_url, self._supabase_key)
		figure_urls: dict[str, str] = {}

		for figure_file in figure_files:
			upload_file = figure_file
			storage_filename = figure_file.name
			is_tmp = False

			if figure_file.suffix.lower() == '.pdf':
				try:
					images = convert_from_path(figure_file, dpi=150, first_page=1, last_page=1)
					if not images:
						raise RuntimeError(f'pdf2image returned no pages for {figure_file}')
					tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
					images[0].save(tmp.name, format='PNG')
					upload_file = Path(tmp.name)
					storage_filename = f'{figure_file.stem}.png'
					is_tmp = True
				except Exception:
					self._logger.warning(
						'Failed to convert PDF figure %s; skipping',
						figure_file,
						exc_info=True,
					)
					continue

			storage_path = f'{paper_id}/{storage_filename}'
			content_type = mimetypes.guess_type(upload_file.name)[0] or 'application/octet-stream'
			try:
				with open(upload_file, 'rb') as f:
					await supabase.storage.from_(self._bucket_name).upload(
						storage_path,
						file=f,
						file_options={
							'content-type': content_type,
							'cache-control': '3600',
							'x-upsert': 'true',
						},
					)
				public_url = await supabase.storage.from_(self._bucket_name).get_public_url(
					storage_path
				)
				figure_urls[storage_filename] = public_url
				self._logger.info('Uploaded figure %s → %s', storage_filename, public_url)
			except Exception:
				self._logger.warning(
					'Failed to upload figure %s, skipping', figure_file.name, exc_info=True
				)
			finally:
				if is_tmp:
					upload_file.unlink(missing_ok=True)

		return figure_urls

	async def upload_figure_bytes(
		self,
		paper_id: str,
		filename: str,
		data: bytes,
		content_type: str = 'image/png',
	) -> str:
		"""Upload raw image bytes to Supabase Storage and return the public URL."""
		storage_path = f'{paper_id}/{filename}'
		supabase = await create_async_client(self._supabase_url, self._supabase_key)

		await supabase.storage.from_(self._bucket_name).upload(
			storage_path,
			file=data,
			file_options={
				'content-type': content_type,
				'cache-control': '3600',
				'x-upsert': 'true',
			},
		)
		public_url = await supabase.storage.from_(self._bucket_name).get_public_url(storage_path)
		self._logger.info('Uploaded figure bytes %s → %s', filename, public_url)
		return public_url

	async def upload_pdf(self, paper_id: str, pdf_path: Path) -> str:
		"""Upload a PDF file to Supabase Storage and return the public URL."""
		storage_path = f'{paper_id}/source.pdf'
		supabase = await create_async_client(self._supabase_url, self._supabase_key)

		with open(pdf_path, 'rb') as f:
			await supabase.storage.from_(self._bucket_name).upload(
				storage_path,
				file=f,
				file_options={
					'content-type': 'application/pdf',
					'cache-control': '3600',
					'x-upsert': 'true',
				},
			)
		public_url = await supabase.storage.from_(self._bucket_name).get_public_url(storage_path)
		self._logger.info('Uploaded PDF %s → %s', pdf_path.name, public_url)
		return public_url
