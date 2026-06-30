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
import { useIsMobile } from '~/hooks/use-mobile'
import { getBlogApiV1BlogPaperIdGet } from '~/api/sdk.gen'
import type { BlogPostResponseSchema } from '~/api/types.gen'
import type { Route } from './+types/blog.$paperId'

const SITE_ORIGIN = 'https://jaxiv.utstudent-scienceblog.com'

// 本文Markdownをレンダリングして表示用データに整形する。loader（サーバー）と
// clientLoader（ブラウザ）の双方から利用する。
async function toBlogPost(data: BlogPostResponseSchema) {
  return {
    ...data,
    contentHtml: await markdownToHtml(data.content),
    requiresAuth: false as const,
  }
}

// サーバーサイドでデータを取得することで、初期HTMLに本文とメタ情報が
// 含まれるようにする（SEO / OGP 対応）。公開記事（arXiv）はこの経路で
// SSR される。一方で非公開記事（PDF）はバックエンドがオーナーの Bearer
// トークン付きリクエストにのみ 200 を返すため、セッションを持たない
// サーバーでは 404 になる。その場合は例外を投げず requiresAuth センチネルを
// 返し、ブラウザ側の clientLoader がユーザーの認証付きで再取得する。
export async function loader({ params }: Route.LoaderArgs) {
  const { data, response } = await getBlogApiV1BlogPaperIdGet({
    baseUrl: import.meta.env.VITE_API_BASE_URL,
    path: { paper_id: params.paperId! },
    throwOnError: false,
  })
  if (data) return toBlogPost(data)
  // 404 は「存在しない」と「非公開（オーナー限定）」を区別できないため、
  // ブラウザ側で認証付き再取得に委ねる。それ以外は本当のエラー。
  if (response.status === 404) return { requiresAuth: true as const }
  throw new Response('Failed to load blog post', {
    status: response.status || 500,
  })
}

// ブラウザ側ではユーザーの Supabase セッションを注入する既定クライアントで
// 取得する。公開記事はサーバーで取得済みなので、その結果をそのまま使う。
export async function clientLoader({
  serverLoader,
  params,
}: Route.ClientLoaderArgs) {
  const serverData = await serverLoader()
  if (!serverData.requiresAuth) return serverData

  // 非公開記事（PDF）: オーナーの認証付きで再取得する。
  const { data, error } = await getBlogApiV1BlogPaperIdGet({
    path: { paper_id: params.paperId! },
    throwOnError: false,
  })
  if (!data)
    throw new Response('Blog post not found', {
      status: error ? 404 : 500,
    })
  return toBlogPost(data)
}
clientLoader.hydrate = true as const

export function meta({ loaderData, location }: Route.MetaArgs) {
  // データ未取得、または非公開記事（SEO 不要）の場合は汎用タイトルのみ。
  if (!loaderData || loaderData.requiresAuth)
    return [{ title: 'Blog Post | jaXiv' }]

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

  // 非公開記事（PDF）はサーバーでは取得できず、ハイドレーション後に
  // clientLoader が認証付きで再取得する。その間のフォールバック表示。
  if (loaderData.requiresAuth) {
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
