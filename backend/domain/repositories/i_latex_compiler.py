from abc import ABC, abstractmethod
from domain.entities.compile_setting import CompileSetting
from domain.entities.compile_error import CompileError


class ILatexCompiler(ABC):
    """
    A latex compiler.
    """

    @abstractmethod
    def compile(self, compile_setting: CompileSetting) -> str | CompileError:
        """
        Compile a latex file.

        Args:
            compile_setting (CompileSetting): The compile setting.

        Returns:
            str | CompileError: The path to the compiled pdf file or the error of compile.
            If the compile is successful, return the path to the compiled pdf file.
            If the compile is failed, return the error of compile.

        Examples:
            >>> compile_setting = CompileSetting(
            >>>     source_directory="path/to/source",
            >>>     target_file_name="main.tex",
            >>>     engine="xelatex",
            >>> )
            >>> latex_compiler = LatexCompiler()
            >>> result = latex_compiler.compile(compile_setting)
            >>> if isinstance(result, str):
            >>>     print(f"Compile successful: {result}")
            >>> else:
            >>>     print(f"Compile failed: {result}")
            >>>     print(f"Error message: {result.error_message}")
        """
        pass
