import asyncio
import re
from logging import getLogger

from mistralai import Mistral
from mistralai.models.assistantmessage import AssistantMessage
from mistralai.models.systemmessage import SystemMessage
from mistralai.models.toolmessage import ToolMessage
from mistralai.models.usermessage import UserMessage
from mistralai.types import UNSET, UNSET_SENTINEL

from domain.entities import LatexFile
from domain.errors import TranslationEmptyResultError
from domain.gateways import ILatexTranslator
from domain.services import LatexPreprocessor
from domain.value_objects import TargetLanguage

from infrastructure.mistral.config import get_mistral_config

mistral_config = get_mistral_config()


class MistralLatexTranslator(ILatexTranslator):
	"""Gateway implementation for translating LaTeX using Mistral API."""

	def __init__(self) -> None:
		self._client = Mistral(api_key=mistral_config.mistral_api_key.get_secret_value())
		self._logger = getLogger(__name__)

	async def translate(
		self,
		latex_file: LatexFile,
		target_language: TargetLanguage,
		max_workers: int = 10,
	) -> LatexFile:
		self._logger.info(
			'Begin translating %s: content length %d',
			latex_file.path,
			len(latex_file.content),
		)
		optimized_content = LatexPreprocessor.optimize(latex_file.content)
		sections = self._split_section(optimized_content)
		self._logger.info('Splitted into %d sections', len(sections))
		semaphore = asyncio.Semaphore(max_workers)

		async def translate_section(section: str) -> str:
			if len(section) == 0:
				self._logger.info('Skipping empty section')
				return ''
			async with semaphore:
				self._logger.info('Translating section length %d', len(section))
				messages: list[AssistantMessage | SystemMessage | ToolMessage | UserMessage] = [
					SystemMessage(content=self._system_prompt(target_language)),
					UserMessage(content=self._user_prompt(section)),
				]
				chat_response = await self._client.chat.complete_async(
					model='codestral-2508',
					messages=messages,
					stream=False,
				)
				message_content = chat_response.choices[0].message.content
				if message_content is None or message_content in (
					UNSET,
					UNSET_SENTINEL,
				):
					raise TranslationEmptyResultError()
				if isinstance(message_content, list):
					translated_text = ''.join(str(x) for x in message_content)
				else:
					translated_text = str(message_content)
				if translated_text == '':
					raise TranslationEmptyResultError()
				return self._extract_latex_content(translated_text)

		translated_latex_contents = await asyncio.gather(
			*[translate_section(section) for section in sections]
		)
		return LatexFile(
			path=latex_file.path,
			content='\n'.join(translated_latex_contents),
		)

	@staticmethod
	def _system_prompt(target_language: TargetLanguage) -> str:
		return (
			f'あなたは、{target_language}のLatexの文法を熟知しているLatexの翻訳家です。'
			'与えられたLatexのソースコードを、Latexの文法を崩すことなく、翻訳してください。'
			'# 注意するべきLatexの文法\n'
			'1. コマンドはそのままにしてください。(`\\section`, `\\cite`, `\\begin{}`, `\\ `, math expressions like `$...$`, environments, labels, \\begin{document}, \\end{document}, etc.)\n'
			'2. `%`はlatexにおけるコメントアウトになるので文字として`%`を含めたい場合は`\\%`としてください。\n'
			'3. 数式中の記号 `\\(` `\\)` `$` `&` `\\` `{` `}` は **絶対に削除・全角化しない**。\n'
			'4. `\\label{}` `\\ref{}` `\\cite{}` で括られたキー名は **一文字も変更しない**。\n'
			'5. カスタムコマンドなど、一般的でないコマンドに関連するものは翻訳せず、そのままにしてください。明かに一般的なコマンドで囲まれている文章のみを翻訳してください。\n'
			'6. \\includegraphics は翻訳せず、画像パスをそのままにしてください\n'
			'# 注意事項\n'
			'単なるコマンドの定義ファイルの場合もあるので、その場合はそのままにしてください。\n'
			'# 出力形式\n'
			'```latex\n'
			'{translated_text}\n'
			'```'
		)

	@staticmethod
	def _user_prompt(section: str) -> str:
		return f'# 翻訳対象のlatexコード\n{section}\n'

	@staticmethod
	def _extract_latex_content(translated_text: str) -> str:
		pattern = r'```latex\s*\n(.*?)\n?```'
		match = re.search(pattern, translated_text, re.DOTALL)
		if match:
			return match.group(1).strip()
		pattern = r'<latex>\s*\n?(.*?)\n?</latex>'
		match = re.search(pattern, translated_text, re.DOTALL)
		if match:
			return match.group(1).strip()
		return translated_text.strip()

	@staticmethod
	def _split_section(latex_text: str) -> list[str]:
		pattern = re.compile(r'^\\(?:sub)?section\*?\{.*\}$', re.MULTILINE)
		matches = list(pattern.finditer(latex_text))
		if not matches:
			return [latex_text.strip()]
		blocks = []
		for i, m in enumerate(matches):
			start = m.start()
			end = matches[i + 1].start() if i + 1 < len(matches) else len(latex_text)
			blocks.append(latex_text[start:end].strip())
		pre_text = latex_text[: matches[0].start()].strip()
		if pre_text:
			blocks.insert(0, pre_text)
		return blocks
