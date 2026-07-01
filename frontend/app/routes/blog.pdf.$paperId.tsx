import markdownToHtml from 'zenn-markdown-html'
import { BookOpenIcon } from 'lucide-react'
import { getBlogApiV1BlogPaperIdGet } from '~/api/sdk.gen'
import { BlogPostView } from '~/components/blog/blog-post-view'
import type { Route } from './+types/blog.pdf.$paperId'

// PDF記事（非公開）用ルート。バックエンドはオーナーの Bearer トークン付き
// リクエストにのみ 200 を返すため、ブラウザ側でユーザーの Supabase セッションを
// 注入する既定クライアントを使って取得する（SEO は不要）。
export async function clientLoader({ params }: Route.ClientLoaderArgs) {
  const { data, error } = await getBlogApiV1BlogPaperIdGet({
    path: { paper_id: params.paperId },
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
    { title: `${loaderData.title} | jaXiv` },
    { name: 'description', content: loaderData.summary },
    // 非公開記事のためクローラーには公開しない。
    { name: 'robots', content: 'noindex' },
  ]
}

export default function PdfBlogPage({
  loaderData,
  params,
}: Route.ComponentProps) {
  return <BlogPostView post={loaderData} paperId={params.paperId} />
}
