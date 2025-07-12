from typing import Final
import re

# クリティカルなエラーパターン（重要度順）
CRITICAL_ERROR_PATTERNS: Final[list[str]] = [
    r"LaTeX Error:",  # LaTeX Error: で始まる行
    r"! LaTeX Error:",  # ! LaTeX Error: で始まる行
    r"! Package .+ Error:",  # ! Package xxx Error:
    r"! Undefined control sequence",  # 未定義コマンド
    r"Runaway argument",  # 無限ループ
    r"! Missing",  # Missing系エラー
    r".*Error.*",  # 大文字のErrorが含まれる行
]

# エラーの文脈として含める最大行数
CONTEXT_LINES: Final[int] = 2


def extract_critical_latex_errors(log_text: str) -> str:
    """
    LaTeXログファイルからクリティカルなエラーを抽出し、文章として返す。
    input: logファイルのテキスト
    output: クリティカルなエラーのみをまとめたテキスト
    """
    lines = log_text.splitlines()
    error_blocks = []

    for i, line in enumerate(lines):
        # 重要なエラーパターンにマッチするかチェック
        is_critical_error = False
        for pattern in CRITICAL_ERROR_PATTERNS:
            if re.search(pattern, line):
                is_critical_error = True
                break

        if is_critical_error:
            # 前後の文脈も含めて抽出
            start = max(0, i - CONTEXT_LINES)
            end = min(len(lines), i + CONTEXT_LINES + 1)
            block = lines[start:end]
            block_text = "\n".join(block).strip()

            # 重複チェック（似たようなエラーブロックは除外）
            is_duplicate = False
            for existing_block in error_blocks:
                if block_text in existing_block or existing_block in block_text:
                    is_duplicate = True
                    break

            if not is_duplicate:
                error_blocks.append(block_text)

    if not error_blocks:
        return "No critical LaTeX errors found."

    return "\n\n--- LaTeX Error ---\n\n".join(error_blocks)


def replace_html_entities_with_latex_commands(latex_content: str) -> str:
    """
    HTMLエンティティをLaTeXコマンドに置換する。
    input: 処理対象のLaTeXソースコード
    output: LaTeXコマンドに置換されたLaTeXソースコード

    Examples:
        >>> content = "<section>Title<bracket><bracket><bracket><bracket>Text here"
        >>> replace_html_entities_with_latex_commands(content)
        "\\section{Title}{}{}{}{}Text here"
    """

    # 2. <bracket>を{に置換する
    latex_content = latex_content.replace("<br>", "{")

    # 3. </bracket>を}に置換する
    latex_content = latex_content.replace("</br>", "}")

    latex_content = latex_content.replace("<math>", "$")

    return latex_content
