import markdownToHtml from 'zenn-markdown-html'
import { useEffect } from 'react'
import { useParams } from 'react-router'
import { BlogPaperChat } from '~/components/blog-paper-chat'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs'
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '~/components/ui/resizable'
import { useIsMobile } from '~/hooks/use-mobile'
import { getBlogApiV1BlogPaperIdGet } from '~/api/sdk.gen'
import type { Route } from './+types/blog.$paperId'

const SITE_ORIGIN = 'https://jaxiv.utstudent-scienceblog.com'

// サーバーサイドでデータを取得することで、初期HTMLに本文とメタ情報が
// 含まれるようにする（SEO / OGP 対応）。公開記事のため認証は不要なので、
// ベースURLを明示して既定クライアントの認証コールバックに依存しない。
export async function loader({ params }: Route.LoaderArgs) {
  const { data, error } = await getBlogApiV1BlogPaperIdGet({
    baseUrl: import.meta.env.VITE_API_BASE_URL,
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

export function meta({ loaderData, location }: Route.MetaArgs) {
  if (!loaderData) return [{ title: 'Blog Post | jaXiv' }]

  const url = `${SITE_ORIGIN}${location.pathname}`
  const title = `${loaderData.title} | jaXiv`
  const description = loaderData.summary

  return [
    { title },
    { name: 'description', content: description },
    // Open Graph
    { property: 'og:type', content: 'article' },
    { property: 'og:title', content: title },
    { property: 'og:description', content: description },
    { property: 'og:url', content: url },
    { property: 'og:site_name', content: 'jaXiv' },
    // Twitter Card
    { name: 'twitter:card', content: 'summary_large_image' },
    { name: 'twitter:title', content: title },
    { name: 'twitter:description', content: description },
    // 正規URL
    { tagName: 'link', rel: 'canonical', href: url },
    // 構造化データ（学術記事）
    {
      'script:ld+json': {
        '@context': 'https://schema.org',
        '@type': 'ScholarlyArticle',
        headline: loaderData.title,
        abstract: description,
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

export default function BlogPage({ loaderData }: Route.ComponentProps) {
  const { paperId } = useParams()
  const isMobile = useIsMobile()

  useEffect(() => {
    import('zenn-embed-elements')
  }, [])

  const blogPanel = (
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
              className="text-sm text-primary hover:underline"
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
  )

  const pdfPanel = (
    <div className="mx-auto flex min-h-0 w-full max-w-3xl flex-1 flex-col">
      <iframe
        title="論文PDF"
        src={loaderData.source_url ?? ''}
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
            {paperId ? <BlogPaperChat paperId={paperId} /> : null}
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
          {paperId ? <BlogPaperChat paperId={paperId} /> : null}
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  )
}
