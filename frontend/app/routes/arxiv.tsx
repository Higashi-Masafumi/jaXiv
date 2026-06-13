import { Suspense, useEffect } from 'react'
import { Await, Link, useNavigate } from 'react-router'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { ArrowRightIcon, SparklesIcon } from 'lucide-react'

import { useAuth } from '~/contexts/auth-context'
import { useBlogStream } from '../hooks/use-blog-stream'
import { listBlogsApiV1BlogGet } from '~/api/sdk.gen'
import { GenerationHero } from '../components/generation-hero'
import { GenerationSteps } from '../components/generation-steps'
import { BlogCardSkeleton } from '~/components/blog/blog-card-skeleton'
import { BlogPostCard } from '~/components/blog/blog-post-card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import {
  Form,
  FormField,
  FormItem,
  FormControl,
  FormMessage,
} from '../components/ui/form'
import type { Route } from './+types/arxiv'

const RECENT_COUNT = 6

const arxivIdSchema = z.object({
  paperId: z
    .string()
    .trim()
    .regex(
      /^\d{4}\.\d{4,5}(v\d+)?$/,
      '有効なarXiv IDを入力してください（例: 2301.00001）',
    ),
})

export function meta() {
  return [
    { title: 'jaXiv — arXiv paper to blog' },
    {
      name: 'description',
      content: 'arXiv 論文を読みやすいブログ記事に変換します。',
    },
  ]
}

export function clientLoader() {
  const recent = listBlogsApiV1BlogGet({
    baseUrl: import.meta.env.VITE_API_BASE_URL,
    query: { page: 1, page_size: RECENT_COUNT },
  }).then(({ data, error }) => {
    if (error || !data) throw new Response('Failed to load recent blogs')
    return data.items
  })
  return { recent }
}

export default function Arxiv({ loaderData }: Route.ComponentProps) {
  const navigate = useNavigate()
  const { isAnonymous, isPaid, signInWithGoogle } = useAuth()
  const { status, steps, error, paperId, startArxivStream } = useBlogStream()

  const form = useForm<z.infer<typeof arxivIdSchema>>({
    resolver: zodResolver(arxivIdSchema),
    defaultValues: { paperId: '' },
  })

  useEffect(() => {
    if (status === 'complete' && paperId) {
      navigate(`/blog/${paperId}`)
    }
  }, [status, paperId, navigate])

  function handleSubmit(values: z.infer<typeof arxivIdSchema>) {
    startArxivStream(values.paperId)
  }

  const isStreaming = status === 'streaming'

  return (
    <main className="h-full overflow-y-auto bg-background">
      <GenerationHero
        icon={SparklesIcon}
        badge="AI で論文を瞬時にブログへ変換"
        titleLead="arXiv 論文を、"
        titleHighlight="読みやすいブログに。"
        description={
          <>
            arXiv ID を入力するだけで、AI
            が論文の内容を日本語ブログ記事に変換します。
            <br className="hidden sm:block" />
            難しい英語論文も、すらすら読める記事になって届きます。
          </>
        }
      >
        <div className="mt-7">
          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(handleSubmit)}
              className="rounded-2xl border border-border/80 bg-white/90 p-5 shadow-lg shadow-indigo-100/40 backdrop-blur-sm dark:bg-card/90 dark:shadow-none"
            >
              <FormField
                control={form.control}
                name="paperId"
                render={({ field }) => (
                  <FormItem>
                    <div className="flex flex-col gap-2.5 sm:flex-row">
                      <FormControl>
                        <Input
                          type="text"
                          placeholder="arXiv ID（例: 2301.00001）"
                          disabled={isStreaming}
                          className="h-11 rounded-xl border-border/70 bg-background text-sm shadow-sm sm:flex-1 sm:text-base"
                          {...field}
                        />
                      </FormControl>
                      <Button
                        type="submit"
                        disabled={isStreaming}
                        size="lg"
                        className="h-11 gap-1.5 rounded-xl px-6 font-semibold sm:w-44"
                      >
                        {isStreaming ? (
                          <>
                            <span className="inline-block size-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                            生成中...
                          </>
                        ) : (
                          <>
                            ブログを生成
                            <ArrowRightIcon className="size-4" />
                          </>
                        )}
                      </Button>
                    </div>
                    <FormMessage className="mt-1.5 text-xs" />
                  </FormItem>
                )}
              />

              <GenerationSteps steps={steps} />

              {error === 'limit_exceeded' ? (
                <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-300">
                  {isAnonymous ? (
                    <span>
                      無料生成回数（3回）を使い切りました。
                      <button
                        type="button"
                        onClick={signInWithGoogle}
                        className="ml-1 font-semibold underline underline-offset-2"
                      >
                        Googleでログイン
                      </button>
                      すると月10回まで生成できます。
                    </span>
                  ) : isPaid ? (
                    <span>
                      今月の生成回数（100回）に達しました。来月のリセットまでお待ちください。
                    </span>
                  ) : (
                    <span>
                      今月の生成回数（10回）を使い切りました。
                      <Link
                        to="/pricing"
                        className="ml-1 font-semibold underline underline-offset-2"
                      >
                        有料プランにアップグレード
                      </Link>
                      すると月100回まで生成できます。
                    </span>
                  )}
                </div>
              ) : error ? (
                <p className="mt-3 text-sm text-destructive">{error}</p>
              ) : null}
            </form>
          </Form>
        </div>
      </GenerationHero>

      {/* Recent Blogs Section */}
      <div className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold tracking-wide text-muted-foreground uppercase">
            最近のブログ
          </h2>
          <Link
            to="/blog"
            className="flex items-center gap-1 text-sm font-medium text-primary transition-colors hover:text-primary/80"
          >
            すべて見る
            <ArrowRightIcon className="size-3.5" />
          </Link>
        </div>

        <Suspense
          fallback={
            <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 3 }, (_, i) => (
                <li key={i}>
                  <BlogCardSkeleton />
                </li>
              ))}
            </ul>
          }
        >
          <Await resolve={loaderData.recent} errorElement={null}>
            {items =>
              items.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-border px-6 py-12 text-center">
                  <p className="text-sm text-muted-foreground">
                    まだブログがありません。上の入力から最初の 1
                    本を生成しましょう。
                  </p>
                </div>
              ) : (
                <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {items.map(post => (
                    <li key={post.paper_id}>
                      <BlogPostCard post={post} />
                    </li>
                  ))}
                </ul>
              )
            }
          </Await>
        </Suspense>
      </div>
    </main>
  )
}
