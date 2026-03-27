import re


class LatexPreprocessor:
	"""Domain Service for preprocessing LaTeX content before translation."""

	@staticmethod
	def optimize(latex_content: str) -> str:
		"""
		Optimize LaTeX source by removing comments and excessive line breaks.

		Args:
		    latex_content: The raw LaTeX source content.

		Returns:
		    The optimized LaTeX source content.
		"""
		cleaned = LatexPreprocessor._remove_comment_lines(latex_content)
		cleaned = LatexPreprocessor._remove_excessive_line_breaks(cleaned)
		return cleaned

	@staticmethod
	def _remove_excessive_line_breaks(
		latex_content: str, max_consecutive_breaks: int = 2
	) -> str:
		if not latex_content:
			return latex_content
		pattern = r'\n{' + str(max_consecutive_breaks + 1) + r',}'
		return re.sub(pattern, '\n' * max_consecutive_breaks, latex_content)

	@staticmethod
	def _remove_comment_lines(latex_content: str) -> str:
		if not latex_content:
			return latex_content
		filtered_lines = [
			line for line in latex_content.split('\n') if not re.match(r'^\s*%', line)
		]
		return '\n'.join(filtered_lines)
