// ブログ記事の遷移先パス。PDF由来の記事（paper_idが`pdf-`接頭）は認証が必要な
// 専用ルートへ、arXiv記事はSSR対応の公開ルートへ振り分ける。
export function blogPostPath(paperId: string): string {
  return paperId.startsWith('pdf-')
    ? `/blog/pdf/${paperId}`
    : `/blog/${paperId}`
}
