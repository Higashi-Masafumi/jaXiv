from domain.repositories import ILatexCompiler
from domain.entities.compile_setting import CompileSetting
from domain.entities.compile_error import CompileError, CompileErrorType
from utils.postprocess import extract_critical_latex_errors
from logging import getLogger
import subprocess
import os


class LatexCompiler(ILatexCompiler):
    """
    A latex compiler.
    """

    def __init__(self):
        self._logger = getLogger(__name__)

    def compile(self, compile_setting: CompileSetting) -> str | CompileError:
        self._logger.info(
            f"Compiling {compile_setting.target_file_name} with {compile_setting.engine}"
        )
        target_file_path = os.path.join(
            compile_setting.source_directory, compile_setting.target_file_name
        )
        log_file_path = os.path.join(
            compile_setting.source_directory,
            compile_setting.target_file_name.replace(".tex", ".log"),
        )
        with open(target_file_path, "r") as f:
            content = f.read()
        content = content.replace(
            "\\begin{document}",
            "\\usepackage[whole]{bxcjkjatype}\n\\begin{document}",
        )
        with open(target_file_path, "w") as f:
            f.write(content)

        cmd = [
            "latexmk",
            "-pdf",
            "-f",
            "-bibtex" if compile_setting.use_bibtex else "",
            compile_setting.target_file_name,
        ]

        self._logger.info(f"Executing command: {cmd}")
        try:
            result = subprocess.run(
                cmd,
                cwd=compile_setting.source_directory,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="utf-8",
                timeout=60,
                errors="ignore",
            )
            self._logger.info(
                f"Latex compilation completed successfully {result.stdout}"
            )
            if result.stderr:
                self._logger.warning(
                    f"Latex compilation completed with warnings: {result.stderr}"
                )
        except subprocess.CalledProcessError as e:
            self._logger.warning(
                f"Error compiling {compile_setting.target_file_name}: {e}"
            )
            return self._handle_error(e, log_file_path)
        except subprocess.TimeoutExpired as e:
            self._logger.error(
                f"Timeout compiling {compile_setting.target_file_name}: {e}"
            )
            return self._handle_error(e, log_file_path)

        self._logger.info(f"Compiled {compile_setting.target_file_name}")
        # compileして生成されたpdfファイルのパスを返す
        pdf_path = target_file_path.replace(".tex", ".pdf")

        # PDFファイルが実際に生成されたかチェック
        if not os.path.exists(pdf_path):
            return CompileError(
                error_type=CompileErrorType.COMPILE_ERROR,
                error_message=f"Compile was successful, but PDF file was not generated: {pdf_path}",
            )

        return pdf_path

    @staticmethod
    def _handle_error(
        error: subprocess.CalledProcessError | subprocess.TimeoutExpired,
        log_file_path: str,
    ) -> CompileError:
        """
        Handle the error of latex compilation.

        Args:
            log_file_path (str): The path to the log file.

        Returns:
            CompileError: The error of latex compilation.
        """
        with open(log_file_path, "r", encoding="utf-8", errors="replace") as f:
            log_content = f.read()
        error_details = extract_critical_latex_errors(log_content)

        if isinstance(error, subprocess.CalledProcessError):
            return CompileError(
                error_type=CompileErrorType.COMPILE_ERROR,
                error_message=error_details,
            )
        elif isinstance(error, subprocess.TimeoutExpired):
            return CompileError(
                error_type=CompileErrorType.COMPILE_TIMEOUT,
                error_message=error_details,
            )
