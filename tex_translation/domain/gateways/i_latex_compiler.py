from abc import ABC, abstractmethod

from domain.value_objects import CompileSetting


class ILatexCompiler(ABC):
    """Gateway for compiling LaTeX files into PDF."""

    @abstractmethod
    def compile(self, compile_setting: CompileSetting) -> str:
        """Compile a LaTeX source tree and return the path to the produced PDF.

        Raises:
            LatexCompilationError: If compilation fails.
            LatexCompilationTimeoutError: If compilation times out.
            PdfNotGeneratedError: If the PDF is not generated.
        """
