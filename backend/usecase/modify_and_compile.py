from domain.repositories import ILatexCompiler, ILatexModifier, IEventStreamer
from domain.entities import ArxivPaperId, CompileError, CompileSetting, LatexFile
from logging import getLogger


class ModifyAndCompileUsecase:
    def __init__(self, latex_compiler: ILatexCompiler, latex_modifier: ILatexModifier):
        self._logger = getLogger(__name__)
        self._latex_compiler = latex_compiler
        self._latex_modifier = latex_modifier

    async def execute(
        self,
        arxiv_paper_id: ArxivPaperId,
        compile_setting: CompileSetting,
        latex_files: list[LatexFile],
        compile_error: CompileError,
        event_streamer: IEventStreamer,
    ) -> str:
        self._logger.info(
            f"Modify and compile the latex files: {compile_setting.target_file_name}"
        )
        await event_streamer.stream_event(
            event_type="progress",
            message="コンパイルに失敗したので、翻訳したtexファイルを修正します。",
            arxiv_paper_id=arxiv_paper_id.root,
        )

        modified_latex_files: list[LatexFile] = []
        for latex_file in latex_files:
            modified_latex_file = await self._latex_modifier.modify(
                latex_file=latex_file,
                compile_error=compile_error,
            )
            modified_latex_files.append(modified_latex_file)

        # 修正したtexファイルを保存
        for latex_file in modified_latex_files:
            self._logger.info(f"Saving the modified latex file: {latex_file.path}")
            with open(latex_file.path, "w", encoding="utf-8") as f:
                f.write(latex_file.content)

        self._logger.info(f"Modified the latex files: {modified_latex_files}")
        await event_streamer.stream_event(
            event_type="progress",
            message="修正したtexファイルをコンパイルします。",
            arxiv_paper_id=arxiv_paper_id.root,
        )

        result = self._latex_compiler.compile(compile_setting)

        if isinstance(result, CompileError):
            await event_streamer.stream_event(
                event_type="failed",
                message=f"修正後のtexファイルのコンパイルに失敗しました。\n{result.error_message}",
                arxiv_paper_id=arxiv_paper_id.root,
            )
            raise Exception(result.error_message)

        return result
