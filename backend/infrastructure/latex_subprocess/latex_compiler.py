import os
import subprocess
from logging import getLogger

from domain.errors import LatexCompilationError, LatexCompilationTimeoutError, PdfNotGeneratedError
from domain.gateways import ILatexCompiler
from domain.value_objects import CompileSetting


class LatexCompiler(ILatexCompiler):
	"""Gateway implementation for compiling LaTeX via latexmk subprocess."""

	def __init__(self):
		self._logger = getLogger(__name__)

	def compile(self, compile_setting: CompileSetting) -> str:
		self._logger.info(
			'Compiling %s with %s', compile_setting.target_file_name, compile_setting.engine
		)

		# Inject CJK support
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

		self._logger.info('Executing command: %s', cmd)
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
			self._logger.info('Latex compilation completed successfully %s', result.stdout)
			if result.stderr:
				self._logger.warning(
					'Latex compilation completed with warnings: source_directory=%s, '
					'target_file_name=%s, stderr=%s',
					compile_setting.source_directory,
					compile_setting.target_file_name,
					result.stderr,
				)
		except subprocess.CalledProcessError as e:
			self._logger.error('Error compiling %s: %s', compile_setting.target_file_name, e)
			raise LatexCompilationError(compile_setting.target_file_name, str(e)) from e
		except subprocess.TimeoutExpired as e:
			self._logger.error('Timeout compiling %s: %s', compile_setting.target_file_name, e)
			raise LatexCompilationTimeoutError(compile_setting.target_file_name) from e

		self._logger.info('Compiled %s', compile_setting.target_file_name)
		pdf_file_name = compile_setting.target_file_name.replace('.tex', '.pdf')
		pdf_file_path = f'{compile_setting.source_directory}/{pdf_file_name}'
		if not os.path.exists(pdf_file_path):
			raise PdfNotGeneratedError(pdf_file_path)
		return pdf_file_path
