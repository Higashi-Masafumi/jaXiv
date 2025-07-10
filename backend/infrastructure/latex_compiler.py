from domain.repositories import ILatexCompiler
from domain.entities.compile_setting import CompileSetting
from logging import getLogger
import subprocess
import os


class LatexCompiler(ILatexCompiler):
    """
    A latex compiler.
    """

    def __init__(self):
        self._logger = getLogger(__name__)

    def compile(self, compile_setting: CompileSetting) -> str:
        self._logger.info(
            f"Compiling {compile_setting.target_file_name} with {compile_setting.engine}"
        )
        # 日本語のようなCJK言語を使うため\usepackage{CJK}を追加する
        target_file_path = os.path.join(
            compile_setting.source_directory, compile_setting.target_file_name
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
            "-bibtex" if compile_setting.use_bibtex else "",
            "-pdf",
            "-interaction=nonstopmode",
            "-file-line-error",
            "-f",
            compile_setting.target_file_name,
        ]

        self._logger.info(f"Executing command: {cmd}")
        subprocess.run(
            cmd,
            cwd=compile_setting.source_directory,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self._logger.info(f"Compiled {compile_setting.target_file_name}")
        # compileして生成されたpdfファイルのパスを返す
        pdf_file_name = compile_setting.target_file_name.replace(".tex", ".pdf")
        return f"{compile_setting.source_directory}/{pdf_file_name}"
