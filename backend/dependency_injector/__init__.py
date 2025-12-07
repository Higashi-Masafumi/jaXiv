import os

from dotenv import load_dotenv

from infrastructure.arxiv_api import ArxivSourceFetcher
from infrastructure.latex_subprocess import LatexCompiler
from infrastructure.mistral import MistralLatexTranslator
from infrastructure.postgres import PostgresTranslatedArxivRepository
from infrastructure.supabase import SupabaseStorageRepository
from usecase import (
    ArxivRedirecter,
    SaveTranslatedArxivUsecase,
    TranslateArxivPaper,
)

load_dotenv()

# --------------------------------------
# 環境変数の取得
# -------------------------------------
postgres_url = os.getenv("POSTGRES_URL")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
bucket_name = os.getenv("BUCKET_NAME")
mistral_api_key = os.getenv("MISTRAL_API_KEY")

if (
    postgres_url is None
    or supabase_url is None
    or supabase_key is None
    or bucket_name is None
    or mistral_api_key is None
):
    raise ValueError("One or more required environment variables are not set")

# --------------------------------------
# 依存関係の解決
# --------------------------------------
arxiv_redirect_usecase = ArxivRedirecter(
    translated_arxiv_repository=PostgresTranslatedArxivRepository(
        postgres_url=postgres_url
    )
)
translate_arxiv_usecase = TranslateArxivPaper(
    arxiv_source_fetcher=ArxivSourceFetcher(),
    latex_compiler=LatexCompiler(),
    latex_translator=MistralLatexTranslator(
        api_key=mistral_api_key,
    ),
)
save_translated_arxiv_usecase = SaveTranslatedArxivUsecase(
    translated_arxiv_repository=PostgresTranslatedArxivRepository(
        postgres_url=postgres_url
    ),
    file_storage_repository=SupabaseStorageRepository(
        supabase_url=supabase_url, supabase_key=supabase_key, bucket_name=bucket_name
    ),
    arxiv_source_fetcher=ArxivSourceFetcher(),
)


# --------------------------------------
# Depends用の関数群
# --------------------------------------
def get_arxiv_redirecter() -> ArxivRedirecter:
    return arxiv_redirect_usecase


def get_translate_arxiv_paper() -> TranslateArxivPaper:
    return translate_arxiv_usecase


def get_save_translated_arxiv() -> SaveTranslatedArxivUsecase:
    return save_translated_arxiv_usecase
