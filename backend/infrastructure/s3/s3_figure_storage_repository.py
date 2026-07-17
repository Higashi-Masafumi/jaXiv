import mimetypes
import tempfile
from logging import getLogger
from pathlib import Path
from typing import ClassVar

import fitz

from domain.repositories import IFigureStorageRepository
from infrastructure.s3.client import build_public_url, create_s3_client
from infrastructure.s3.config import get_s3_storage_config

# 図PNGのレンダリング解像度。トリミングの閾値ではなく出力画質の設定。
FIGURE_RENDER_DPI = 150


def render_pdf_figure_to_png(pdf_path: Path) -> bytes:
	"""Render a figure PDF's first page to PNG, cropped to its actual content.

	LaTeX の ``\\includegraphics`` が図PDFの内容領域だけを表示するのに倣い、ページ
	全面ではなく実際に描画されている内容(テキスト・ベクター・埋め込み画像)の外接
	矩形だけをラスタライズする。余白除去はピクセルの明度閾値ではなく内容のベクター
	座標から厳密に決めるため(pdfcrop 相当)、tolerance や padding といった決め打ちの
	定数を持たない。内容が検出できない場合はページ全体を描画する。
	"""
	with fitz.open(pdf_path) as doc:
		page = doc[0]

		content: fitz.Rect | None = None
		rects = [drawing['rect'] for drawing in page.get_drawings()]
		rects += [block['bbox'] for block in page.get_text('dict')['blocks']]
		rects += [image['bbox'] for image in page.get_image_info()]
		for raw_rect in rects:
			rect = fitz.Rect(raw_rect)
			if rect.is_empty or rect.is_infinite:
				continue
			content = rect if content is None else content | rect

		clip = page.rect if content is None else content & page.rect
		if clip.is_empty:
			clip = page.rect

		zoom = FIGURE_RENDER_DPI / 72.0
		pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip, colorspace=fitz.csRGB)
		return pix.tobytes('png')


class S3FigureStorageRepository(IFigureStorageRepository):
	"""Uploads figures from a LaTeX source directory to an S3-compatible store (e.g. R2)."""

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
		self._config = get_s3_storage_config()
		self._bucket_name = self._config.blog_figures_bucket_name
		self._public_base_url = self._config.blog_figures_public_base_url
		self._logger = getLogger(__name__)

	async def upload_figures(self, paper_id: str, source_dir: Path) -> dict[str, str]:
		"""
		Upload all figure files from source_dir to S3-compatible storage.

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
		figure_urls: dict[str, str] = {}

		async with create_s3_client(self._config) as s3:
			for figure_file in figure_files:
				upload_file = figure_file
				storage_filename = figure_file.name
				is_tmp = False

				if figure_file.suffix.lower() == '.pdf':
					try:
						png_bytes = render_pdf_figure_to_png(figure_file)
						tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
						tmp.write(png_bytes)
						tmp.close()
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
				content_type = (
					mimetypes.guess_type(upload_file.name)[0] or 'application/octet-stream'
				)
				try:
					await s3.put_object(
						Bucket=self._bucket_name,
						Key=storage_path,
						Body=upload_file.read_bytes(),
						ContentType=content_type,
						CacheControl='3600',
					)
					public_url = build_public_url(self._public_base_url, storage_path)
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
		"""Upload raw image bytes to S3-compatible storage and return the public URL."""
		storage_path = f'{paper_id}/{filename}'
		async with create_s3_client(self._config) as s3:
			await s3.put_object(
				Bucket=self._bucket_name,
				Key=storage_path,
				Body=data,
				ContentType=content_type,
				CacheControl='3600',
			)
		public_url = build_public_url(self._public_base_url, storage_path)
		self._logger.info('Uploaded figure bytes %s → %s', filename, public_url)
		return public_url

	async def upload_pdf(self, paper_id: str, pdf_path: Path) -> str:
		"""Upload a PDF file to S3-compatible storage and return the public URL."""
		storage_path = f'{paper_id}/source.pdf'
		async with create_s3_client(self._config) as s3:
			await s3.put_object(
				Bucket=self._bucket_name,
				Key=storage_path,
				Body=pdf_path.read_bytes(),
				ContentType='application/pdf',
				CacheControl='3600',
			)
		public_url = build_public_url(self._public_base_url, storage_path)
		self._logger.info('Uploaded PDF %s → %s', pdf_path.name, public_url)
		return public_url
