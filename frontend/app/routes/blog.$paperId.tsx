import markdownToHtml from 'zenn-markdown-html'
import { getBlogApiV1BlogPaperIdGet } from '~/api/sdk.gen'
import { BlogPostView } from '~/components/blog/blog-post-view'
import type { Route } from './+types/blog.$paperId'

const SITE_ORIGIN = 'https://jaxiv.utstudent-scienceblog.com'

// 記事本文（Markdown）中に埋め込まれた図版URLのうち、OGP/Twitterカードで
// レンダリング可能な形式の最初の1枚を抽出する。図はarXivのソースからアップ
// ロードされたものをそのまま使うため、`.eps`/`.svg`のようにXやFacebookの
// クローラーが画像として展開できない形式が混ざりうる（`.pdf`のみバックエンドで
// PNGに変換済み）。対応形式以外はスキップし、後続の図にフォールバックする。
const MARKDOWN_IMAGE_RE = /!\[[^\]]*\]\((https?:\/\/[^\s)]+)\)/g
const SUPPORTED_CARD_IMAGE_EXTENSIONS = /\.(?:png|jpe?g|gif|webp)(?:[?#]|$)/i

function extractFirstImageUrl(markdown: string): string | undefined {
  const urls = markdown.matchAll(MARKDOWN_IMAGE_RE)
  for (const [, url] of urls) {
    if (SUPPORTED_CARD_IMAGE_EXTENSIONS.test(url)) return url
  }
  return undefined
}

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
  const imageUrl = loaderData.ogImageUrl

  return [
    { title },
    { name: 'description', content: description },
    // Open Graph
    { property: 'og:type', content: 'article' },
    { property: 'og:title', content: title },
    { property: 'og:description', content: description },
    { property: 'og:url', content: url },
    { property: 'og:site_name', content: 'jaXiv' },
    ...(imageUrl ? [{ property: 'og:image', content: imageUrl }] : []),
    // Twitter Card
    {
      name: 'twitter:card',
      content: imageUrl ? 'summary_large_image' : 'summary',
    },
    { name: 'twitter:title', content: title },
    { name: 'twitter:description', content: description },
    ...(imageUrl ? [{ name: 'twitter:image', content: imageUrl }] : []),
    // 正規URL
    { tagName: 'link', rel: 'canonical', href: url },
    // 構造化データ（学術記事）
    {
      'script:ld+json': {
        '@context': 'https://schema.org',
        '@type': 'ScholarlyArticle',
        headline: loaderData.title,
        abstract: description,
        image: imageUrl ?? undefined,
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
