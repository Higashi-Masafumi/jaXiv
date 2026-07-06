import { listBlogsApiV1BlogGet } from '~/api/sdk.gen'
import { SITE_ORIGIN } from '~/lib/site'
import { escapeXml } from '~/lib/xml'

// 静的に載せたい主要ページ（公開ページのみ）
const STATIC_PATHS = ['/', '/blog', '/pricing']

// sitemap取得時の1ページあたり件数。総数が多くてもページングで全件巡回する。
const PAGE_SIZE = 100

// sitemap.xml リソースルート。default コンポーネントを持たず loader だけで
// XMLを返す。公開されている全arXiv記事（/blog/:paperId）と主要静的ページを列挙し、
// 記事の増減が自動で反映されるようAPIをページングして全件取得する。
export async function loader() {
  const baseUrl = import.meta.env.VITE_API_BASE_URL
  const paperIds: string[] = []

  // 1ページ目で total_pages を確認しつつ全ページを巡回する。
  let page = 1
  let totalPages = 1
  do {
    const { data, error } = await listBlogsApiV1BlogGet({
      baseUrl,
      query: { page, page_size: PAGE_SIZE },
      throwOnError: false,
    })
    // 取得失敗時は部分的なsitemapを200で返す（1時間キャッシュされる）のではなく
    // 5xxを返してクローラに再試行させる。
    if (error || !data)
      throw new Response('Failed to build sitemap', { status: 503 })
    for (const item of data.items) paperIds.push(item.paper_id)
    totalPages = data.total_pages
    page += 1
  } while (page <= totalPages)

  const urls = [
    ...STATIC_PATHS.map(p => `${SITE_ORIGIN}${p}`),
    ...paperIds.map(id => `${SITE_ORIGIN}/blog/${escapeXml(id)}`),
  ]

  const body =
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
    urls.map(u => `  <url><loc>${u}</loc></url>`).join('\n') +
    `\n</urlset>\n`

  return new Response(body, {
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
      // Cloudflareでのキャッシュ（1時間）。運用に応じて調整可。
      'Cache-Control': 'public, max-age=3600',
    },
  })
}
