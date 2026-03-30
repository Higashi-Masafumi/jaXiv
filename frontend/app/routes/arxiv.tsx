import { useEffect } from 'react'
import { useNavigate } from 'react-router'

import { useBlogStream } from '../hooks/use-blog-stream'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'

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
  const { status, steps, error, paperId, startArxivStream } = useBlogStream()

  useEffect(() => {
    if (status === 'complete' && paperId) {
      navigate(`/blog/${paperId}`)
    }
  }, [status, paperId, navigate])

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const id =
      new FormData(e.currentTarget).get('paperId')?.toString().trim() ?? ''
    if (!id) return
    startArxivStream(id)
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

        <form
          onSubmit={handleSubmit}
          className="w-full rounded-2xl border border-hero-card-border/70 bg-hero-card/80 p-5 shadow-2xl backdrop-blur-sm sm:p-6"
        >
          <div className="flex flex-col gap-3 sm:flex-row">
            <Input
              type="text"
              name="paperId"
              placeholder="arXiv ID（例: 2301.00001）"
              disabled={isStreaming}
              className="border-input bg-background text-foreground placeholder:text-muted-foreground sm:flex-1"
            />
            <Button
              type="submit"
              disabled={isStreaming}
              className="bg-hero-accent font-semibold text-primary-foreground transition-colors hover:bg-hero-accent/90 sm:w-40"
            >
              {isStreaming ? '生成中...' : 'ブログを生成'}
            </Button>
          </div>

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

          {error && <p className="mt-3 text-sm text-destructive">{error}</p>}
        </form>
      </section>
    </main>
  )
}
