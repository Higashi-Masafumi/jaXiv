from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from domain.gateways import IArxivSourceFetcher, ILatexCompiler, ILatexTranslator
from infrastructure.arxiv_api import ArxivSourceFetcher
from infrastructure.latex_subprocess import LatexCompiler
from infrastructure.mistral import MistralLatexTranslator
from usecase import TranslateArxivPaperUseCase


@lru_cache
def get_arxiv_source_fetcher() -> IArxivSourceFetcher:
    return ArxivSourceFetcher()


@lru_cache
def get_latex_compiler() -> ILatexCompiler:
    return LatexCompiler()


@lru_cache
def get_latex_translator() -> ILatexTranslator:
    return MistralLatexTranslator()


def get_translate_arxiv_paper_use_case(
    arxiv_source_fetcher: Annotated[
        IArxivSourceFetcher, Depends(get_arxiv_source_fetcher)
    ],
    latex_compiler: Annotated[ILatexCompiler, Depends(get_latex_compiler)],
    latex_translator: Annotated[ILatexTranslator, Depends(get_latex_translator)],
) -> TranslateArxivPaperUseCase:
    return TranslateArxivPaperUseCase(
        arxiv_source_fetcher=arxiv_source_fetcher,
        latex_compiler=latex_compiler,
        latex_translator=latex_translator,
    )
