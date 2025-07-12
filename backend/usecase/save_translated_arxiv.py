from domain.repositories import (
    IArxivSourceFetcher,
    IFileStorageRepository,
    ITranslatedArxivRepository,
    IEventStreamer,
)
from domain.entities import (
    ArxivPaperId,
    ArxivPaperMetadataWithTranslatedUrl,
    TranslatedPdfFile,
)
from logging import getLogger
from pydantic import HttpUrl
from pathlib import Path
import shutil


class SaveTranslatedArxivUsecase:
    """
    Save a translated arxiv paper.
    """

    def __init__(
        self,
        translated_arxiv_repository: ITranslatedArxivRepository,
        file_storage_repository: IFileStorageRepository,
        arxiv_source_fetcher: IArxivSourceFetcher,
    ):
        self._logger = getLogger(__name__)
        self._translated_arxiv_repository = translated_arxiv_repository
        self._file_storage_repository = file_storage_repository
        self._arxiv_source_fetcher = arxiv_source_fetcher

    async def save_translated_arxiv(
        self,
        arxiv_paper_id: ArxivPaperId,
        translated_arxiv_pdf_path: str,
        event_streamer: IEventStreamer,
    ) -> ArxivPaperMetadataWithTranslatedUrl:
        """
        Save a translated arxiv paper.

        Args:
            arxiv_paper_id (ArxivPaperId): The ID of the paper to save.
            translated_arxiv_pdf_path (str): The path to the translated arxiv pdf file.

        Returns:
            ArxivPaperMetadataWithTranslatedUrl: The metadata of the saved paper.
        """
        self._logger.info("Saving translated arxiv paper %s", arxiv_paper_id)
        # 1. 論文のメタデータを取得
        arxiv_paper_metadata = self._arxiv_source_fetcher.fetch_paper_metadata(
            paper_id=arxiv_paper_id
        )
        # 進捗をストリーミング
        await event_streamer.stream_event(
            event_type="progress",
            message=f"Arxiv {arxiv_paper_id} のメタデータの取得を完了しました。",
            arxiv_paper_id=arxiv_paper_id.root,
        )

        # 2. 翻訳済み論文のpdfを保存する
        self._logger.info("Saving translated arxiv paper %s", arxiv_paper_id)
        translated_latex_file = TranslatedPdfFile(
            path=translated_arxiv_pdf_path,
            storage_path=f"{arxiv_paper_id.root}_translated.pdf",
        )
        translated_arxiv_pdf_url = (
            await self._file_storage_repository.save_translated_latex_file_and_get_url(
                translated_latex_file=translated_latex_file
            )
        )
        # pdf_pathの親ディレクトリを削除する
        shutil.rmtree(Path(translated_arxiv_pdf_path).parent)
        # 進捗をストリーミング
        await event_streamer.stream_event(
            event_type="progress",
            message=f"Arxiv {arxiv_paper_id} の翻訳済み論文のpdfを保存しました。",
            arxiv_paper_id=arxiv_paper_id.root,
        )

        # 3. 論文のメタデータを更新
        arxiv_paper_metadata_with_translated_url = ArxivPaperMetadataWithTranslatedUrl(
            **arxiv_paper_metadata.model_dump(),
            translated_file_storage_path=translated_latex_file.storage_path,
            translated_url=HttpUrl(translated_arxiv_pdf_url),
        )

        # 4. 論文のメタデータを保存
        self._logger.info("Saving translated arxiv paper metadata %s", arxiv_paper_id)
        self._translated_arxiv_repository.save_translated_paper_metadata(
            translated_paper_metadata=arxiv_paper_metadata_with_translated_url
        )
        # 進捗をストリーミング
        await event_streamer.stream_event(
            event_type="completed",
            message=f"Arxiv {arxiv_paper_id} の翻訳済み論文のメタデータを保存しました。翻訳済みのpdfを表示します。",
            arxiv_paper_id=arxiv_paper_id.root,
            translated_pdf_url=HttpUrl(translated_arxiv_pdf_url),
        )

        return arxiv_paper_metadata_with_translated_url
