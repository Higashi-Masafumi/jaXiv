import { useEffect } from 'react'
import { BlogPaperChat } from '~/components/blog-paper-chat'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs'
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '~/components/ui/resizable'
import { useIsMobile } from '~/hooks/use-mobile'
import type { BlogPostResponseSchema } from '~/api/types.gen'

export type BlogPostWithHtml = BlogPostResponseSchema & { contentHtml: string }

// arXiv記事（SSR）とPDF記事（clientLoader）で共通の表示コンポーネント。
export function BlogPostView({
  post,
  paperId,
}: {
  post: BlogPostWithHtml
  paperId: string
}) {
  const isMobile = useIsMobile()

  useEffect(() => {
    import('zenn-embed-elements')
  }, [])

  const blogPanel = (
    <div className="mx-auto max-w-3xl">
      {(post.authors.length > 0 || post.source_url) && (
        <header className="mb-8 space-y-2">
          {post.authors.length > 0 && (
            <p className="text-sm text-muted-foreground">
              {post.authors.join(', ')}
            </p>
          )}
          {post.source_url && (
            <a
              href={post.source_url}
              target="_blank"
              rel="noreferrer"
              className="text-sm text-primary hover:underline"
            >
              {post.source_url}
            </a>
          )}
        </header>
      )}

      <div
        className="znc"
        dangerouslySetInnerHTML={{ __html: post.contentHtml }}
      />
    </div>
  )

  const pdfPanel = (
    <div className="mx-auto flex min-h-0 w-full max-w-3xl flex-1 flex-col">
      <iframe
        title="論文PDF"
        src={post.source_url ?? ''}
        className="min-h-0 w-full flex-1 border-0"
      />
    </div>
  )

  // Mobile: a single column with the chat as a third tab. The side-by-side
  // resizable split is unusable below ~768px.
  if (isMobile) {
    return (
      <div className="h-svh overflow-hidden">
        <Tabs
          defaultValue="blog"
          className="flex h-full min-h-0 flex-col gap-3 px-4 pb-2 pt-3"
        >
          <TabsList
            variant="line"
            className="h-9 w-full shrink-0 justify-start pl-10"
          >
            <TabsTrigger value="blog">ブログ</TabsTrigger>
            <TabsTrigger value="pdf">PDF</TabsTrigger>
            <TabsTrigger value="chat">アシスタント</TabsTrigger>
          </TabsList>

          <TabsContent
            value="blog"
            className="mt-0 min-h-0 flex-1 overflow-y-auto data-[state=inactive]:hidden"
          >
            {blogPanel}
          </TabsContent>

          <TabsContent
            value="pdf"
            className="mt-0 flex min-h-0 flex-1 flex-col overflow-hidden data-[state=inactive]:hidden"
          >
            {pdfPanel}
          </TabsContent>

          <TabsContent
            value="chat"
            className="mt-0 -mx-4 flex min-h-0 flex-1 flex-col overflow-hidden border-t border-border/40 data-[state=inactive]:hidden"
          >
            <BlogPaperChat paperId={paperId} />
          </TabsContent>
        </Tabs>
      </div>
    )
  }

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
                {blogPanel}
              </TabsContent>

              <TabsContent
                value="pdf"
                className="mt-0 flex min-h-0 flex-1 flex-col overflow-hidden data-[state=inactive]:hidden"
              >
                {pdfPanel}
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
          <BlogPaperChat paperId={paperId} />
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  )
}
