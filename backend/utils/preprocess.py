import re


def optimize_latex_content(latex_content: str) -> str:
    """
    LaTeXソースコードを最適化する。
    1. コメント行を削除
    2. 不要な改行を削除
    3. 行末の空白を削除

    Args:
        latex_content: 処理対象のLaTeXソースコード

    Returns:
        最適化されたLaTeXソースコード

    Examples:
        >>> content = "\\section{Title}\\n\\n\\n\\n\\nText here"
        >>> optimize_latex_content(content)
        "\\section{Title}\\n\\nText here"
    """
    cleaned_content = remove_comment_lines(latex_content)
    cleaned_content = remove_excessive_line_breaks(cleaned_content)
    return cleaned_content


def remove_excessive_line_breaks(
    latex_content: str, max_consecutive_breaks: int = 2
) -> str:
    """
    LaTeXソースコードから不要な改行を取り除く。

    Args:
        latex_content: 処理対象のLaTeXソースコード
        max_consecutive_breaks: 許可する最大連続改行数（デフォルト: 2）

    Returns:
        不要な改行が除去されたLaTeXソースコード

    Examples:
        >>> content = "\\section{Title}\\n\\n\\n\\n\\nText here"
        >>> remove_excessive_line_breaks(content)
        "\\section{Title}\\n\\nText here"
    """
    if not latex_content:
        return latex_content

    # 3個以上の連続する改行を2個の改行に置換
    pattern = r"\n{" + str(max_consecutive_breaks + 1) + r",}"
    cleaned_content = re.sub(pattern, "\n" * max_consecutive_breaks, latex_content)

    return cleaned_content


def clean_trailing_spaces(latex_content: str) -> str:
    """
    各行の末尾の不要な空白文字を除去する。

    Args:
        latex_content: 処理対象のLaTeXソースコード

    Returns:
        行末の空白が除去されたLaTeXソースコード
    """
    if not latex_content:
        return latex_content

    lines = latex_content.split("\n")
    cleaned_lines = [line.rstrip() for line in lines]
    return "\n".join(cleaned_lines)


def remove_comment_lines(latex_content: str) -> str:
    """
    LaTeXソースコードから、行頭が`%`（もしくは空白＋`%`）で始まるコメント行を削除する。

    Args:
        latex_content: 処理対象のLaTeXソースコード

    Returns:
        コメント行が取り除かれたLaTeXソースコード
    """
    if not latex_content:
        return latex_content

    # 各行を調べ、行頭が `%` または空白＋`%` で始まるものを除外
    filtered_lines = [
        line for line in latex_content.split("\n") if not re.match(r"^\s*%", line)
    ]
    return "\n".join(filtered_lines)
