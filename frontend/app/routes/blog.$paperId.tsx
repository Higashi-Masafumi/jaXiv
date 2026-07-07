import markdownToHtml from 'zenn-markdown-html'
import { getBlogApiV1BlogPaperIdGet } from '~/api/sdk.gen'
import { BlogPostView } from '~/components/blog/blog-post-view'
import { extractFirstImageUrl } from '~/lib/blog-content'
import { SITE_ORIGIN } from '~/lib/site'
import type { Route } from './+types/blog.$paperId'

// arXiv記事（公開）用ルート。サーバーサイドで取得して初期HTMLに本文と
// メタ情報を含めることで SEO / OGP に対応する。PDF記事（非公開）は認証が必要な
// 専用ルート `/blog/pdf/:paperId` で扱い、遷移リンクは `source_type` で振り分ける。
export async function loader({ params }: Route.LoaderArgs) {
  const { data, error } = await getBlogApiV1BlogPaperIdGet({
    baseUrl: import.meta.env.VITE_API_BASE_URL,
    path: { paper_id: params.paperId },
    throwOnError: false,
  })
  if (!data)
    throw new Response('Blog post not found', {
      status: error ? 404 : 500,
    })
  return {
    ...data,
    contentHtml: await markdownToHtml(data.content),
    ogImageUrl: extractFirstImageUrl(data.content),
  }
}

export function meta({ loaderData, location }: Route.MetaArgs) {
  if (!loaderData) return [{ title: 'Blog Post | jaXiv' }]

  const url = `${SITE_ORIGIN}${location.pathname}`
  const title = `${loaderData.title} | jaXiv`
  const description = loaderData.summary
  // 図がない記事はブランドロゴをサムネイルにして、画像なしカードを避ける
  const imageUrl = loaderData.ogImageUrl ?? `${SITE_ORIGIN}/icon-512.png`

  return [
    { title },
    { name: 'description', content: description },
    // Open Graph
    { property: 'og:type', content: 'article' },
    { property: 'og:title', content: title },
    { property: 'og:description', content: description },
    { property: 'og:url', content: url },
    { property: 'og:site_name', content: 'jaXiv' },
    { property: 'og:image', content: imageUrl },
    // Twitter Card: 左サムネイル+右テキストの summary 形式に固定する。
    // summary_large_image はX上でタイトル・説明文が表示されないため使わない。
    { name: 'twitter:card', content: 'summary' },
    { name: 'twitter:title', content: title },
    { name: 'twitter:description', content: description },
    { name: 'twitter:image', content: imageUrl },
    // 正規URL
    { tagName: 'link', rel: 'canonical', href: url },
    // 構造化データ（学術記事）
    {
      'script:ld+json': {
        '@context': 'https://schema.org',
        '@type': 'ScholarlyArticle',
        headline: loaderData.title,
        abstract: description,
        // 構造化データには記事本来の図版のみを載せる（ロゴは記事画像ではない）
        image: loaderData.ogImageUrl,
        inLanguage: 'ja',
        author:
          loaderData.authors.length > 0
            ? loaderData.authors.map(name => ({ '@type': 'Person', name }))
            : undefined,
        url,
        sameAs: loaderData.source_url ?? undefined,
      },
    },
  ]
}

export default function BlogPage({ loaderData, params }: Route.ComponentProps) {
  return <BlogPostView post={loaderData} paperId={params.paperId} />
}
