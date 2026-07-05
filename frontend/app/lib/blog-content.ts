const MARKDOWN_IMAGE_RE = /!\[[^\]]*\]\((https?:\/\/[^\s)]+)\)/

// og:image/twitter:image用に、記事本文Markdown中の最初の図版URLを抽出する。
export function extractFirstImageUrl(markdown: string): string | undefined {
  return MARKDOWN_IMAGE_RE.exec(markdown)?.[1]
}
