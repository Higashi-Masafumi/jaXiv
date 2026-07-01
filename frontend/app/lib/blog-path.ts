import type { BlogPostResponseSchema } from '~/api/types.gen'

type BlogSourceType = BlogPostResponseSchema['source_type']

// ブログ記事の遷移先パス。PDF由来の記事は認証が必要な専用ルートへ、arXiv記事は
// SSR対応の公開ルートへ振り分ける。種別はbackendの`source_type`で判定する
// （paper_idの形式に依存しないため、ID形式が変わっても壊れない）。
export function blogPostPath(
  paperId: string,
  sourceType: BlogSourceType,
): string {
  return sourceType === 'pdf' ? `/blog/pdf/${paperId}` : `/blog/${paperId}`
}
