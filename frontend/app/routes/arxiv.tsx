import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

import { useAuth } from '~/contexts/auth-context'
import { useBlogStream } from '../hooks/use-blog-stream'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import {
  Form,
  FormField,
  FormItem,
  FormControl,
  FormMessage,
} from '../components/ui/form'

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

export default function Arxiv() {
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
    <main className="relative min-h-[calc(100vh-3rem)] overflow-hidden bg-hero-background px-4 py-16 text-hero-foreground">
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute -left-20 top-10 h-72 w-72 rounded-full bg-hero-accent-soft/20 blur-3xl" />
        <div className="absolute -right-24 bottom-12 h-80 w-80 rounded-full bg-hero-accent-secondary-soft/20 blur-3xl" />
        <div className="absolute inset-0 bg-gradient-to-b from-hero-accent/10 via-transparent to-transparent" />
      </div>

      <section className="mx-auto flex w-full max-w-2xl flex-col items-center gap-8">
        <div className="space-y-4 text-center">
          <p className="mx-auto w-fit rounded-full border border-hero-accent/30 bg-hero-accent/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-hero-accent">
            AI Research Companion
          </p>
          <h1 className="text-5xl font-black tracking-tight sm:text-6xl">
            jaXiv
          </h1>
          <p className="mx-auto max-w-xl text-base leading-relaxed text-hero-muted sm:text-lg">
            arXiv 論文を読みやすいブログ記事に変換します。まずは paper ID
            を入力して、要点をすぐに把握しましょう。
          </p>
        </div>

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(handleSubmit)}
            className="w-full rounded-2xl border border-hero-card-border/70 bg-hero-card/80 p-5 shadow-2xl backdrop-blur-sm sm:p-6"
          >
            <FormField
              control={form.control}
              name="paperId"
              render={({ field }) => (
                <FormItem>
                  <div className="flex flex-col gap-3 sm:flex-row">
                    <FormControl>
                      <Input
                        type="text"
                        placeholder="arXiv ID（例: 2301.00001）"
                        disabled={isStreaming}
                        className="border-input bg-background text-foreground placeholder:text-muted-foreground sm:flex-1"
                        {...field}
                      />
                    </FormControl>
                    <Button
                      type="submit"
                      disabled={isStreaming}
                      className="bg-hero-accent font-semibold text-primary-foreground transition-colors hover:bg-hero-accent/90 sm:w-40"
                    >
                      {isStreaming ? '生成中...' : 'ブログを生成'}
                    </Button>
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />

            {steps.length > 0 && (
              <ul className="mt-4 space-y-1.5 text-sm">
                {steps.map((step, i) => (
                  <li
                    key={i}
                    className={`flex items-center gap-2 transition-opacity ${step.done ? 'text-muted-foreground' : 'text-foreground'}`}
                  >
                    {step.done ? (
                      <span className="text-hero-accent">✓</span>
                    ) : (
                      <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-hero-accent border-t-transparent" />
                    )}
                    <span className={step.done ? 'line-through' : ''}>
                      {step.message}
                    </span>
                  </li>
                ))}
              </ul>
            )}

            {error === 'limit_exceeded' ? (
              <div className="mt-3 rounded-lg border border-hero-accent/40 bg-hero-accent/10 px-4 py-3 text-sm">
                {isAnonymous ? (
                  <span>
                    今月の無料生成回数（3回）を使い切りました。
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
      </section>
    </main>
  )
}
