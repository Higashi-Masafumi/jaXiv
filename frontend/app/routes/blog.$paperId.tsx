import markdownToHtml from 'zenn-markdown-html'
import { useEffect } from 'react'

import { getBlogApiV1BlogArxivArxivPaperIdGet } from '../api/sdk.gen'
import type { Route } from './+types/blog.$paperId'

// SSR loader はサーバーで動くので process.env を参照する
const SERVER_API_BASE = process.env.API_BASE_URL ?? 'http://localhost:8001'

export async function loader({ params }: Route.LoaderArgs) {
  const { data, error } = await getBlogApiV1BlogArxivArxivPaperIdGet({
    baseUrl: SERVER_API_BASE,
    path: { arxiv_paper_id: params.paperId! },
  })
  if (error) throw new Response('Blog post not found', { status: 404 })
  return {
    ...data,
    contentHtml: await markdownToHtml(data.content),
  }
}

export function meta({ loaderData }: Route.MetaArgs) {
  if (!loaderData) return [{ title: 'Blog Post | jaXiv' }]
  return [
    { title: `${loaderData.title} | jaXiv` },
    { name: 'description', content: loaderData.summary.slice(0, 160) },
  ]
}

export default function BlogPage({ loaderData }: Route.ComponentProps) {
  useEffect(() => {
    import('zenn-embed-elements')
  }, [])
  return (
    <main className="max-w-3xl mx-auto px-4 py-8">
      <header className="mb-8 space-y-2">
        <p className="text-sm text-muted-foreground">
          {loaderData.authors.join(', ')}
        </p>
        <a
          href={loaderData.source_url}
          target="_blank"
          rel="noreferrer"
          className="text-sm text-blue-600 hover:underline"
        >
          arXiv: {loaderData.paper_id}
        </a>
      </header>

      <div
        className="znc"
        dangerouslySetInnerHTML={{ __html: loaderData.contentHtml }}
      />
    </main>
  )
}
