import markdownToHtml from 'zenn-markdown-html'
import { BookOpenIcon } from 'lucide-react'
import { useEffect } from 'react'
import { useParams } from 'react-router'
import { BlogPaperChat } from '~/components/blog-paper-chat'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs'
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '~/components/ui/resizable'
import { getBlogApiV1BlogPaperIdGet } from '~/api/sdk.gen'
import type { Route } from './+types/blog.$paperId'

export async function clientLoader({ params }: Route.ClientLoaderArgs) {
  const { data, error } = await getBlogApiV1BlogPaperIdGet({
    path: { paper_id: params.paperId! },
    throwOnError: false,
  })
  if (!data)
    throw new Response('Blog post not found', {
      status: error ? 404 : 500,
    })
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
          <div className="flex h-full min-h-0 flex-col px-4 py-8">
            <Tabs
              defaultValue="blog"
              className="flex min-h-0 flex-1 flex-col gap-4"
            >
              <TabsList
                variant="line"
                className="h-9 w-full max-w-md shrink-0 justify-start"
              >
                <TabsTrigger value="blog">ブログ</TabsTrigger>
                <TabsTrigger value="pdf">PDF</TabsTrigger>
              </TabsList>

              <TabsContent
                value="blog"
                className="mt-0 min-h-0 flex-1 overflow-y-auto data-[state=inactive]:hidden"
              >
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
              </TabsContent>

              <TabsContent
                value="pdf"
                className="mt-0 flex min-h-0 flex-1 flex-col overflow-hidden data-[state=inactive]:hidden"
              >
                <div className="mx-auto flex min-h-0 w-full max-w-3xl flex-1 flex-col">
                  <iframe
                    title="論文PDF"
                    src={loaderData.source_url ?? ''}
                    className="min-h-0 w-full flex-1 border-0"
                  />
                </div>
              </TabsContent>
            </Tabs>
          </div>
        </ResizablePanel>

        <ResizableHandle withHandle />

        <ResizablePanel
          defaultSize={38}
          minSize={20}
          className="min-h-0 overflow-hidden"
        >
          {paperId ? <BlogPaperChat paperId={paperId} /> : null}
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  )
}
