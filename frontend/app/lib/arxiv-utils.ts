/**
 * arXiv URLからIDを抽出する
 * @param url arXivのURL
 * @returns arXiv ID（例: "2405.12345"）またはnull
 */
export function extractArxivId(url: string): string | null {
  try {
    // URLのパターン:
    // - https://arxiv.org/abs/2405.12345
    // - https://arxiv.org/pdf/2405.12345.pdf
    // - https://arxiv.org/abs/2405.12345v1
    // - http://arxiv.org/abs/2405.12345
    // または単純にIDのみ: 2405.12345

    // URLをトリムして正規化
    const trimmedUrl = url.trim();

    // arXiv IDのパターン（古い形式と新しい形式に対応）
    // 新形式: YYMM.NNNNN (例: 2405.12345)
    // 古形式: category/YYMMNNN (例: cs.AI/0704123)
    const arxivIdPattern =
      /(?:(?:https?:\/\/)?arxiv\.org\/(?:abs|pdf)\/)?([a-zA-Z\-]+(?:\.[a-zA-Z\-]+)*\/\d{7}|\d{4}\.\d{4,5})(?:v\d+)?(?:\.pdf)?$/;

    const match = trimmedUrl.match(arxivIdPattern);

    if (match && match[1]) {
      return match[1];
    }

    // パターンにマッチしない場合はnullを返す
    return null;
  } catch (error) {
    console.error("Error extracting arXiv ID:", error);
    return null;
  }
}

/**
 * arXiv IDが有効かどうかを検証する
 * @param id arXiv ID
 * @returns 有効な場合true
 */
export function isValidArxivId(id: string): boolean {
  // 新形式: YYMM.NNNNN
  const newFormatPattern = /^\d{4}\.\d{4,5}$/;
  // 古形式: category/YYMMNNN
  const oldFormatPattern = /^[a-zA-Z\-]+(?:\.[a-zA-Z\-]+)*\/\d{7}$/;

  return newFormatPattern.test(id) || oldFormatPattern.test(id);
}
