import markdownToHtml from 'zenn-markdown-html'
import { useEffect } from 'react'

import { getBlogApiV1BlogPaperIdGet } from '../api/sdk.gen'
import { CLIENT_API_BASE } from '../lib/api-config'
import type { Route } from './+types/blog.$paperId'
import { Skeleton } from '../components/ui/skeleton'

export async function clientLoader({ params }: Route.LoaderArgs) {
  const { data, error } = await getBlogApiV1BlogPaperIdGet({
    baseUrl: CLIENT_API_BASE,
    path: { paper_id: params.paperId! },
  })
  if (error) throw new Response('Blog post not found', { status: 404 })
  return {
    ...data,
    contentHtml: await markdownToHtml(data.content),
  }
}

export function HydrateFallback() {
  return (
    <main className="max-w-3xl mx-auto px-4 py-8">
      <Skeleton className="h-10 w-full" />
    </main>
  )
}
export function meta({ loaderData }: Route.MetaArgs) {
  if (!loaderData) return [{ title: 'Blog Post | jaXiv' }]
  return [
    { title: loaderData.title },
    { name: 'description', content: loaderData.summary },
  ]
}

export default function BlogPage({ loaderData }: Route.ComponentProps) {
  useEffect(() => {
    import('zenn-embed-elements')
  }, [])
  return (
    <main className="max-w-3xl mx-auto px-4 py-8">
      {(loaderData.authors.length > 0 || loaderData.source_url) && (
        <header className="mb-8 space-y-2">
          {loaderData.authors.length > 0 && (
            <p className="text-sm text-muted-foreground">
              {loaderData.authors.join(', ')}
            </p>
          )}
          {loaderData.source_url && (
            <a
              href={loaderData.source_url}
              target="_blank"
              rel="noreferrer"
              className="text-sm text-blue-600 hover:underline"
            >
              {loaderData.source_url}
            </a>
          )}
        </header>
      )}

      <div
        className="znc"
        dangerouslySetInnerHTML={{ __html: loaderData.contentHtml }}
      />
    </main>
  )
}
