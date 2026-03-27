import { Form, redirect, useNavigation } from 'react-router'

import { generateBlogApiV1BlogArxivArxivPaperIdPost } from '../api/sdk.gen'
import type { Route } from './+types/home'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'

// clientAction はブラウザで動くので import.meta.env を参照する
const BROWSER_API_BASE =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8001'

export function meta() {
  return [
    { title: 'jaXiv — arXiv paper to blog' },
    {
      name: 'description',
      content:
        'Convert arXiv papers into readable blog posts powered by Gemini.',
    },
  ]
}

export async function clientAction({ request }: Route.ClientActionArgs) {
  const formData = await request.formData()
  const paperId = (formData.get('paperId') as string | null)?.trim() ?? ''
  if (!paperId) return { error: 'arXiv ID を入力してください' }

  const { error } = await generateBlogApiV1BlogArxivArxivPaperIdPost({
    baseUrl: BROWSER_API_BASE,
    path: { arxiv_paper_id: paperId },
  })
  if (error) {
    const detail = (error as { detail?: string }).detail
    return { error: detail ?? 'ブログの生成に失敗しました' }
  }

  return redirect(`/blog/${paperId}`)
}

export default function Home({ actionData }: Route.ComponentProps) {
  const navigation = useNavigation()
  const isSubmitting = navigation.state === 'submitting'

  return (
    <main className="flex flex-col items-center justify-center min-h-screen px-4 gap-8">
      <div className="text-center space-y-2">
        <h1 className="text-4xl font-bold tracking-tight">jaXiv</h1>
        <p className="text-muted-foreground">
          arXiv 論文をブログ記事に変換します
        </p>
      </div>

      <Form method="post" className="flex flex-col gap-3 w-full max-w-md">
        <Input
          type="text"
          name="paperId"
          placeholder="arXiv ID（例: 2301.00001）"
          disabled={isSubmitting}
        />
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? '生成中...' : 'ブログを生成'}
        </Button>
        {actionData?.error && (
          <p className="text-destructive text-sm text-center">
            {actionData.error}
          </p>
        )}
      </Form>
    </main>
  )
}
