import { useState } from 'react'
import { Form, redirect, useNavigation } from 'react-router'

import {
  generateBlogApiV1BlogArxivArxivPaperIdPost,
  generateBlogFromPdfApiV1BlogPdfPost,
} from '../api/sdk.gen'
import type { Route } from './+types/home'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'

const SERVER_API_BASE = process.env.API_BASE_URL ?? 'http://localhost:8001'

export function meta() {
  return [
    { title: 'jaXiv — arXiv paper to blog' },
    {
      name: 'description',
      content: 'Convert arXiv papers into readable blog posts powered by Gemini.',
    },
  ]
}

export async function action({ request }: Route.ActionArgs) {
  const formData = await request.formData()
  const intent = formData.get('intent') as string

  if (intent === 'arxiv') {
    const paperId = (formData.get('paperId') as string | null)?.trim() ?? ''
    if (!paperId) return { error: 'arXiv ID を入力してください', intent }

    const { data, error } = await generateBlogApiV1BlogArxivArxivPaperIdPost({
      baseUrl: SERVER_API_BASE,
      path: { arxiv_paper_id: paperId },
    })
    if (error) {
      const detail = (error as { detail?: string }).detail
      return { error: detail ?? 'ブログの生成に失敗しました', intent }
    }
    return redirect(`/blog/${data.paper_id}`)
  }

  if (intent === 'pdf') {
    const file = formData.get('file') as File | null
    if (!file || file.size === 0) return { error: 'PDFファイルを選択してください', intent }

    const backendForm = new FormData()
    backendForm.append('file', file)

    const response = await fetch(`${SERVER_API_BASE}/api/v1/blog/pdf`, {
      method: 'POST',
      body: backendForm,
    })
    if (!response.ok) {
      const body = await response.json().catch(() => ({}))
      const detail = (body as { detail?: string }).detail
      return { error: detail ?? 'PDFからのブログ生成に失敗しました', intent }
    }
    const data = await response.json()
    return redirect(`/blog/${data.paper_id}`)
  }

  return { error: '不正なリクエストです', intent: '' }
}

export default function Home({ actionData }: Route.ComponentProps) {
  const navigation = useNavigation()
  const [tab, setTab] = useState<'arxiv' | 'pdf'>('arxiv')

  const isSubmitting = navigation.state === 'submitting'
  const activeIntent = isSubmitting
    ? (navigation.formData?.get('intent') as string | null)
    : null

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
          <h1 className="text-5xl font-black tracking-tight sm:text-6xl">ブログ生成</h1>
          <p className="mx-auto max-w-xl text-base leading-relaxed text-hero-muted sm:text-lg">
            arXiv ID または PDF ファイルから、読みやすいブログ記事を生成します。
          </p>
        </div>

        <div className="w-full rounded-2xl border border-hero-card-border/70 bg-hero-card/80 shadow-2xl backdrop-blur-sm">
          <div className="flex border-b border-border">
            <button
              type="button"
              onClick={() => setTab('arxiv')}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                tab === 'arxiv'
                  ? 'border-b-2 border-primary text-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              arXiv ID
            </button>
            <button
              type="button"
              onClick={() => setTab('pdf')}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                tab === 'pdf'
                  ? 'border-b-2 border-primary text-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              PDF アップロード
            </button>
          </div>

          {tab === 'arxiv' && (
            <Form method="post" encType="multipart/form-data" className="p-5 sm:p-6">
              <input type="hidden" name="intent" value="arxiv" />
              <div className="flex flex-col gap-3 sm:flex-row">
                <Input
                  type="text"
                  name="paperId"
                  placeholder="arXiv ID（例: 2301.00001）"
                  disabled={isSubmitting}
                  className="border-input bg-background text-foreground placeholder:text-muted-foreground sm:flex-1"
                />
                <Button
                  type="submit"
                  disabled={isSubmitting}
                  className="bg-hero-accent font-semibold text-primary-foreground transition-colors hover:bg-hero-accent/90 sm:w-40"
                >
                  {activeIntent === 'arxiv' ? '生成中...' : 'ブログを生成'}
                </Button>
              </div>
              {actionData?.intent === 'arxiv' && actionData.error && (
                <p className="mt-3 text-sm text-destructive">{actionData.error}</p>
              )}
            </Form>
          )}

          {tab === 'pdf' && (
            <Form method="post" encType="multipart/form-data" className="p-5 sm:p-6">
              <input type="hidden" name="intent" value="pdf" />
              <div className="flex flex-col gap-3 sm:flex-row">
                <Input
                  type="file"
                  name="file"
                  accept=".pdf"
                  disabled={isSubmitting}
                  className="border-input bg-background text-foreground sm:flex-1"
                />
                <Button
                  type="submit"
                  disabled={isSubmitting}
                  className="bg-hero-accent font-semibold text-primary-foreground transition-colors hover:bg-hero-accent/90 sm:w-40"
                >
                  {activeIntent === 'pdf' ? '生成中...' : 'ブログを生成'}
                </Button>
              </div>
              {actionData?.intent === 'pdf' && actionData.error && (
                <p className="mt-3 text-sm text-destructive">{actionData.error}</p>
              )}
            </Form>
          )}
        </div>
      </section>
    </main>
  )
}
