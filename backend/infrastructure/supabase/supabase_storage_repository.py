from sqlalchemy.engine import create
from domain.repositories import IFileStorageRepository
from domain.entities.latex_file import TranslatedLatexFile
from supabase import create_async_client
from logging import getLogger


class SupabaseStorageRepository(IFileStorageRepository):
    def __init__(self, supabase_url: str, supabase_key: str, bucket_name: str):
        self._supabase_url = supabase_url
        self._supabase_key = supabase_key
        self._bucket_name = bucket_name
        self._logger = getLogger(__name__)

    async def save_translated_latex_file_and_get_url(
        self, translated_latex_file: TranslatedLatexFile
    ) -> str:
        """
        Save a translated latex file and get the URL of the file.

        Args:
            translated_latex_file (TranslatedLatexFile): The translated latex file to save.

        Returns:
            str: The URL of the saved file.
        """
        self._logger.info(
            "Saving translated latex file %s", translated_latex_file.storage_path
        )
        # 1. クライアントの初期化
        supabase = await create_async_client(self._supabase_url, self._supabase_key)
        # 2. ファイルのアップロード
        with open(translated_latex_file.path, "r") as f:
            response = await supabase.storage.from_(self._bucket_name).upload(
                translated_latex_file.storage_path,
                f.read(),
            )
        # 3. ファイルのURLの取得
        self._logger.info(
            "Saved translated latex file %s", translated_latex_file.storage_path
        )
        response_url = await supabase.storage.from_(self._bucket_name).get_public_url(
            translated_latex_file.storage_path
        )
        return response_url
