import { listBlogsApiV1BlogGet } from '~/api/sdk.gen'
import type { BlogPostResponseSchema } from '~/api/types.gen'
import { SITE_ORIGIN } from '~/lib/site'
import { escapeXml } from '~/lib/xml'

const FEED_TITLE = 'jaXiv'
const FEED_DESCRIPTION = 'arXiv論文をやさしく解説するブログの新着記事'

// feed取得時の1ページあたり件数。総数が多くてもページングで全件巡回する。
const PAGE_SIZE = 100

// フィードに載せる最大件数。RSSは新着中心で良いため上限を設ける。
const MAX_ITEMS = 50

// feed.xml リソースルート。default コンポーネントを持たず loader だけで RSS 2.0 を
// 返す。公開されているarXiv記事（/blog/:paperId）を新着順で配信する。PDF記事は
// 認証必須（/blog/pdf/:paperId）のため除外する。
export async function loader() {
  const baseUrl = import.meta.env.VITE_API_BASE_URL
  const posts: BlogPostResponseSchema[] = []

  // 1ページ目で total_pages を確認しつつ全ページを巡回する。
  let page = 1
  let totalPages = 1
  do {
    const { data, error } = await listBlogsApiV1BlogGet({
      baseUrl,
      query: { page, page_size: PAGE_SIZE },
      throwOnError: false,
    })
    // 取得失敗時は部分的なfeedを200で返さず、5xxでリーダーに再試行させる。
    if (error || !data)
      throw new Response('Failed to build feed', { status: 503 })
    for (const item of data.items) posts.push(item)
    totalPages = data.total_pages
    page += 1
  } while (page <= totalPages)

  // arXiv記事のみを新着順（created_at降順）で最大MAX_ITEMS件配信する。
  // 一覧APIの並び順に依存しないよう、ここで明示的にソートする。
  const items = posts
    .filter(post => post.source_type === 'arxiv')
    .sort((a, b) => b.created_at.localeCompare(a.created_at))
    .slice(0, MAX_ITEMS)

  const itemsXml = items
    .map(post => {
      const link = `${SITE_ORIGIN}/blog/${escapeXml(post.paper_id)}`
      const creator = post.authors.length
        ? `      <dc:creator>${escapeXml(post.authors.join(', '))}</dc:creator>\n`
        : ``
      return (
        `    <item>\n` +
        `      <title>${escapeXml(post.title)}</title>\n` +
        `      <link>${link}</link>\n` +
        `      <guid isPermaLink="true">${link}</guid>\n` +
        `      <description>${escapeXml(post.summary)}</description>\n` +
        creator +
        `      <pubDate>${new Date(post.created_at).toUTCString()}</pubDate>\n` +
        `    </item>`
      )
    })
    .join('\n')

  // channelのlastBuildDateには最新記事の公開日時を使う（記事ゼロ時は省略）。
  const lastBuildDate = items[0]
    ? `    <lastBuildDate>${new Date(items[0].created_at).toUTCString()}</lastBuildDate>\n`
    : ``

  const body =
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/">\n` +
    `  <channel>\n` +
    `    <title>${FEED_TITLE}</title>\n` +
    `    <link>${SITE_ORIGIN}/blog</link>\n` +
    `    <description>${FEED_DESCRIPTION}</description>\n` +
    `    <language>ja</language>\n` +
    `    <atom:link href="${SITE_ORIGIN}/feed.xml" rel="self" type="application/rss+xml" />\n` +
    lastBuildDate +
    (itemsXml ? `${itemsXml}\n` : ``) +
    `  </channel>\n` +
    `</rss>\n`

  return new Response(body, {
    headers: {
      'Content-Type': 'application/rss+xml; charset=utf-8',
      // Cloudflareでのキャッシュ（1時間）。運用に応じて調整可。
      'Cache-Control': 'public, max-age=3600',
    },
  })
}
