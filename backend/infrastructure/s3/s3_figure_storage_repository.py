import math
import mimetypes
import tempfile
from asyncio import get_running_loop
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack, contextmanager
from logging import getLogger
from pathlib import Path
from typing import ClassVar, Final

import fitz

from domain.repositories import IFigureStorageRepository
from infrastructure.s3.client import build_public_url, create_s3_client
from infrastructure.s3.config import get_s3_storage_config

# 図PNGのレンダリング解像度。トリミングの閾値ではなく出力画質の設定。
FIGURE_RENDER_DPI = 150
# 1枚あたりに許すピクセル数の上限。Pixmap は RGB 3バイト/px を一括で確保するうえ、
# PNG 化のワークバッファも同時に載るため、実測でこの数倍が瞬間的な使用量になる。
# 論文の図PDFにはページサイズが 6754x1866pt (≒94インチ幅) といった巨大なものがあり、
# 150DPI をそのまま適用すると 1枚で 160MB超の Pixmap になって 512MB のコンテナが落ちる。
# 上限を超える図は解像度を落として描画し、ピーク使用量をページサイズから独立させる。
FIGURE_MAX_PIXELS = 4_000_000
# ラスタライズ専用のワーカー。プロセス全体で1枚ずつに直列化するため max_workers=1 で
# 固定する。asyncio.to_thread の既定エグゼキュータ(CPU数+4スレッド)へ投げると、同時に
# 走るブログ生成リクエストの数だけ Pixmap が並んで載り、1枚あたりの上限を設けた意味が
# なくなる。溢れた分はキューで待つので、常駐するのは常に1枚分。
_RENDER_EXECUTOR: Final[ThreadPoolExecutor] = ThreadPoolExecutor(
	max_workers=1, thread_name_prefix='figure-render'
)


@contextmanager
def temporary_png_path() -> Iterator[Path]:
	"""Yield a path for a temporary PNG and delete it on exit.

	``with`` で括ることで、アップロード成否だけでなく SSE 切断による
	``CancelledError`` (``except Exception`` を素通りする) でも確実に消える。
	図1枚のPNGは数MBになりうるため、残すとコンテナのディスクを食い潰す。
	"""
	tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
	tmp.close()
	png_path = Path(tmp.name)
	try:
		yield png_path
	finally:
		png_path.unlink(missing_ok=True)


def render_pdf_figure_to_png(pdf_path: Path, dest_path: Path) -> None:
	"""Render a figure PDF's first page to a PNG at ``dest_path``, cropped to its content.

	LaTeX の ``\\includegraphics`` が図PDFの内容領域だけを表示するのに倣い、ページ
	全面ではなく実際に描画されている内容(テキスト・ベクター・埋め込み画像)の外接
	矩形だけをラスタライズする。余白除去はピクセルの明度閾値ではなく内容のベクター
	座標から厳密に決めるため(pdfcrop 相当)、tolerance や padding といった決め打ちの
	定数を持たない。内容が検出できない場合はページ全体を描画する。

	解像度は ``FIGURE_RENDER_DPI`` を上限としつつ、出力が ``FIGURE_MAX_PIXELS`` を
	超える場合はそこに収まるよう縮小する。PNG はメモリ上のバイト列ではなく直接
	ファイルへ書き出す。
	"""
	with fitz.open(pdf_path) as doc:
		page = doc[0]

		content: fitz.Rect | None = None
		# get_text('dict') は画像ブロックの実バイト列まで返すため 'blocks' を使う。
		# 必要なのは外接矩形だけで、写真を貼った図では実バイト列がそのまま無駄な常駐になる。
		rects = [drawing['rect'] for drawing in page.get_drawings()]
		rects += [block[:4] for block in page.get_text('blocks')]
		rects += [image['bbox'] for image in page.get_image_info()]
		for raw_rect in rects:
			rect = fitz.Rect(raw_rect)
			if rect.is_empty or rect.is_infinite:
				continue
			content = rect if content is None else content | rect

		clip = page.rect if content is None else content & page.rect
		if clip.is_empty:
			clip = page.rect

		zoom = min(
			FIGURE_RENDER_DPI / 72.0,
			math.sqrt(FIGURE_MAX_PIXELS / (clip.width * clip.height)),
		)
		pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip, colorspace=fitz.csRGB)
		pix.save(dest_path)


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
				# 一時PNGの後始末を ExitStack に預ける。continue でも例外でも
				# CancelledError でも、この with を抜ける時点で必ず削除される。
				with ExitStack() as cleanup:
					upload_file = figure_file
					storage_filename = figure_file.name

					if figure_file.suffix.lower() == '.pdf':
						upload_file = cleanup.enter_context(temporary_png_path())
						try:
							# ラスタライズは数秒かかる CPU 処理なので、イベントループを
							# 止めないよう専用ワーカーへ逃がす。max_workers=1 なので
							# 同時に載る Pixmap はプロセス全体で常に1枚だけ。
							await get_running_loop().run_in_executor(
								_RENDER_EXECUTOR,
								render_pdf_figure_to_png,
								figure_file,
								upload_file,
							)
						except Exception:
							self._logger.warning(
								'Failed to convert PDF figure %s; skipping',
								figure_file,
								exc_info=True,
							)
							continue
						storage_filename = f'{figure_file.stem}.png'

					storage_path = f'{paper_id}/{storage_filename}'
					content_type = (
						mimetypes.guess_type(upload_file.name)[0] or 'application/octet-stream'
					)
					try:
						# ファイルオブジェクトを渡すと botocore/aiohttp が逐次読み出すため、
						# 図の実体がメモリに丸ごと載らない。
						with upload_file.open('rb') as body:
							await s3.put_object(
								Bucket=self._bucket_name,
								Key=storage_path,
								Body=body,
								ContentType=content_type,
								CacheControl='3600',
							)
					except Exception:
						self._logger.warning(
							'Failed to upload figure %s, skipping', figure_file.name, exc_info=True
						)
						continue

					public_url = build_public_url(self._public_base_url, storage_path)
					figure_urls[storage_filename] = public_url
					self._logger.info('Uploaded figure %s → %s', storage_filename, public_url)

		return figure_urls

	async def upload_figure_file(
		self,
		paper_id: str,
		filename: str,
		image_path: Path,
		content_type: str = 'image/png',
	) -> str:
		"""Stream an image file to S3-compatible storage and return the public URL."""
		storage_path = f'{paper_id}/{filename}'
		async with create_s3_client(self._config) as s3:
			with image_path.open('rb') as body:
				await s3.put_object(
					Bucket=self._bucket_name,
					Key=storage_path,
					Body=body,
					ContentType=content_type,
					CacheControl='3600',
				)
		public_url = build_public_url(self._public_base_url, storage_path)
		self._logger.info('Uploaded figure %s → %s', filename, public_url)
		return public_url

	async def upload_pdf(self, paper_id: str, pdf_path: Path) -> str:
		"""Stream a PDF file to S3-compatible storage and return the public URL."""
		storage_path = f'{paper_id}/source.pdf'
		async with create_s3_client(self._config) as s3:
			with pdf_path.open('rb') as body:
				await s3.put_object(
					Bucket=self._bucket_name,
					Key=storage_path,
					Body=body,
					ContentType='application/pdf',
					CacheControl='3600',
				)
		public_url = build_public_url(self._public_base_url, storage_path)
		self._logger.info('Uploaded PDF %s → %s', pdf_path.name, public_url)
		return public_url
