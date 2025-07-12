from abc import ABC, abstractmethod
from domain.entities.latex_file import LatexFile
from domain.entities.compile_error import CompileError


class ILatexModifier(ABC):
    """
    The interface of latex modifier.
    """

    @abstractmethod
    async def modify(
        self,
        latex_file: LatexFile,
        compile_error: CompileError,
    ) -> LatexFile:
        """
        Modify the latex file.

        Args:
            latex_file: The latex file to modify.
            compile_error: The error of compile.

        Returns:
            The modified latex file.

        Examples:
            >>> latex_file = LatexFile(
            >>>     path="path/to/latex/file.tex",
            >>>     content="",
            >>> )
            >>> compile_error = CompileError(
            >>>     error_type=CompileErrorType.COMPILE_ERROR,
            >>>     error_message="Error message",
            >>> )
            >>> latex_modifier = LatexModifier()
            >>> modified_latex_file = latex_modifier.modify(latex_file, compile_error)
            >>> print(modified_latex_file.content)
        """
        pass
