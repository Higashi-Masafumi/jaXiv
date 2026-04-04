import markdownToHtml from 'zenn-markdown-html'
import { BookOpenIcon } from 'lucide-react'
import { useEffect } from 'react'
import { useParams } from 'react-router'
import { BlogPaperChat } from '~/components/blog-paper-chat'
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '~/components/ui/resizable'
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
    <div className="h-screen overflow-hidden">
      <ResizablePanelGroup orientation="horizontal">
        <ResizablePanel defaultSize={62} minSize={30}>
          <div className="h-full overflow-y-auto px-4 py-8">
            <div className="mx-auto max-w-3xl">
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
            </div>
          </div>
        </ResizablePanel>

        <ResizableHandle withHandle />

        <ResizablePanel defaultSize={38} minSize={20}>
          {paperId ? <BlogPaperChat paperId={paperId} /> : null}
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  )
}
