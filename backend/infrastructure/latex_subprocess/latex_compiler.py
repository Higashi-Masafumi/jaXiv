import os
import subprocess
from logging import getLogger

from domain.entities.compile_setting import CompileSetting
from domain.repositories import ILatexCompiler


class LatexCompiler(ILatexCompiler):
	"""
	A latex compiler.
	"""

	def __init__(self):
		self._logger = getLogger(__name__)

	def compile(self, compile_setting: CompileSetting) -> str:
		self._logger.info(
			f'Compiling {compile_setting.target_file_name} with {compile_setting.engine}'
		)
		# 日本語のようなCJK言語を使うため\usepackage{CJK}を追加する
		target_file_path = os.path.join(
			compile_setting.source_directory, compile_setting.target_file_name
		)
		with open(target_file_path) as f:
			content = f.read()
		content = content.replace(
			'\\begin{document}',
			'\\usepackage[whole]{bxcjkjatype}\n\\begin{document}',
		)
		with open(target_file_path, 'w') as f:
			f.write(content)
		cmd = [
			'latexmk',
			'-bibtex' if compile_setting.use_bibtex else '',
			'-pdf',
			'-interaction=nonstopmode',
			'-file-line-error',
			'-f',
			compile_setting.target_file_name,
		]

		self._logger.info(f'Executing command: {cmd}')
		try:
			result = subprocess.run(
				cmd,
				cwd=compile_setting.source_directory,
				check=False,
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE,
				encoding='utf-8',
				timeout=60,
				errors='ignore',
			)
			self._logger.info(f'Latex compilation completed successfully {result.stdout}')
			if result.stderr:
				self._logger.warning(
					f'Latex compilation completed with warnings: source_directory={compile_setting.source_directory}, target_file_name={compile_setting.target_file_name}, stderr={result.stderr}'
				)
		except subprocess.CalledProcessError as e:
			self._logger.error(f'Error compiling {compile_setting.target_file_name}: {e}')
			raise RuntimeError(f'Error compiling {compile_setting.target_file_name}: {e}')
		except subprocess.TimeoutExpired as e:
			self._logger.error(f'Timeout compiling {compile_setting.target_file_name}: {e}')
			raise RuntimeError(f'Timeout compiling {compile_setting.target_file_name}: {e}')

		self._logger.info(f'Compiled {compile_setting.target_file_name}')
		# compileして生成されたpdfファイルのパスを返す
		pdf_file_name = compile_setting.target_file_name.replace('.tex', '.pdf')
		pdf_file_path = f'{compile_setting.source_directory}/{pdf_file_name}'
		if not os.path.exists(pdf_file_path):
			raise FileNotFoundError(f'PDF file not found: {pdf_file_path}')
		return pdf_file_path
