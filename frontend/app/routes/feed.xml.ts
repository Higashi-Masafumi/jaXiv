import { listBlogsApiV1BlogGet } from '~/api/sdk.gen'
import { SITE_ORIGIN } from '~/lib/site'
import { escapeXml } from '~/lib/xml'

const FEED_TITLE = 'jaXiv'
const FEED_DESCRIPTION = 'arXiv論文をやさしく解説するブログの新着記事'

// フィードに載せる件数。一覧APIは公開arXiv記事をcreated_at降順で返すため、先頭ページを
// この件数だけ取得すれば新着順のフィードになる（page_sizeの上限は100）。
const FEED_SIZE = 50

// feed.xml リソースルート。default コンポーネントを持たず loader だけで RSS 2.0 を
// 返す。一覧APIが公開arXiv記事をcreated_at降順で返す（PDF記事は認証必須で含まれない）
// ため、先頭1ページのみ取得してそのまま配信する。
export async function loader() {
  const { data, error } = await listBlogsApiV1BlogGet({
    baseUrl: import.meta.env.VITE_API_BASE_URL,
    query: { page: 1, page_size: FEED_SIZE },
    throwOnError: false,
  })
  // 取得失敗時は部分的なfeedを200で返さず、5xxでリーダーに再試行させる。
  if (error || !data)
    throw new Response('Failed to build feed', { status: 503 })

  const items = data.items

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
