import markdownToHtml from 'zenn-markdown-html'
import { BookOpenIcon } from 'lucide-react'
import { useEffect } from 'react'
import { useParams } from 'react-router'
import type { UIMessage } from 'ai'

import { BlogPaperChat } from '~/components/blog-paper-chat'
import { getBlogApiV1BlogPaperIdGet } from '../api/sdk.gen'
import type { Route } from './+types/blog.$paperId'

export async function loader({ params }: Route.LoaderArgs) {
  const { data, error } = await getBlogApiV1BlogPaperIdGet({
    baseUrl: process.env.API_BASE_URL,
    path: { paper_id: params.paperId! },
  })
  if (error) throw new Response('Blog post not found', { status: 404 })
  return {
    ...data,
    contentHtml: await markdownToHtml(data.content),
  }
}

export async function action({ request, context, params }: Route.ActionArgs) {
  const { messages }: { messages: UIMessage[] } = await request.json()
  const { createRagChatResponse } = await import('~/lib/rag_agent')
  return createRagChatResponse({
    messages,
    paperId: params.paperId!,
    apiBaseUrl: context.cloudflare.env.API_BASE_URL,
    aiBinding: context.cloudflare.env.AI,
  })
}

export function HydrateFallback() {
  return (
    <main
      className="mx-auto flex min-h-[50vh] max-w-3xl items-center justify-center px-4 py-8"
      aria-busy="true"
    >
      <p className="sr-only">読み込み中</p>
      <BookOpenIcon
        className="size-14 shrink-0 text-muted-foreground animate-pulse"
        aria-hidden
      />
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
  const { paperId } = useParams()
  useEffect(() => {
    import('zenn-embed-elements')
  }, [])
  return (
    <main className="mx-auto flex max-w-7xl flex-col gap-8 px-4 py-8 lg:flex-row lg:items-start lg:gap-10">
      <article className="min-w-0 flex-1 lg:max-w-3xl">
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
      </article>

      {paperId ? (
        <aside className="w-full shrink-0 lg:sticky lg:top-4 lg:w-96">
          <BlogPaperChat paperId={paperId} />
        </aside>
      ) : null}
    </main>
  )
}
