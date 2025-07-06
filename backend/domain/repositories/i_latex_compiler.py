from abc import ABC, abstractmethod
from domain.entities.compile_setting import CompileSetting


class ILatexCompiler(ABC):
    """
    A latex compiler.
    """

    @abstractmethod
    def compile(self, compile_setting: CompileSetting) -> str:
        """
        Compile a latex file.

        Args:
            compile_setting (CompileSetting): The compile setting.

        Returns:
            str: The path to the compiled pdf file.
        """
        pass