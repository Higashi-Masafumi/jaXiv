import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router'
import { ArrowRightIcon, FileUpIcon } from 'lucide-react'

import { useAuth } from '~/contexts/auth-context'
import { useBlogStream } from '../hooks/use-blog-stream'
import { GenerationHero } from '../components/generation-hero'
import { GenerationSteps } from '../components/generation-steps'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'

export function meta() {
  return [
    { title: 'PDF → ブログ生成 | jaXiv' },
    {
      name: 'description',
      content: 'PDF ファイルからブログ記事を生成します。',
    },
  ]
}

export default function Pdf() {
  const navigate = useNavigate()
  const { isAnonymous, isPaid } = useAuth()
  const { status, steps, error, paperId, startPdfStream } = useBlogStream()

  useEffect(() => {
    if (status === 'complete' && paperId) {
      navigate(`/blog/${paperId}`)
    }
  }, [status, paperId, navigate])

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const file = new FormData(e.currentTarget).get('file')
    if (!(file instanceof File)) return
    startPdfStream(file)
  }

  const isStreaming = status === 'streaming'
  const isDisabled = isStreaming || isAnonymous

  return (
    <main className="h-full overflow-y-auto bg-background">
      <GenerationHero
        icon={FileUpIcon}
        badge="PDF を貼るだけでブログ記事に"
        titleLead="PDF 論文を、"
        titleHighlight="読みやすいブログに。"
        description="PDF ファイルをアップロードするだけで、AI が論文の内容を日本語ブログ記事に変換します。"
      >
        {isAnonymous && (
          <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-300">
            PDF生成には
            <Link
              to="/login"
              className="mx-1 font-semibold underline underline-offset-2"
            >
              ログイン
            </Link>
            が必要です。arXiv ID の入力は
            <Link
              to="/"
              className="ml-1 font-semibold underline underline-offset-2"
            >
              ログインなしで利用できます
            </Link>
            。
          </div>
        )}

        <div className="mt-7">
          <form
            onSubmit={handleSubmit}
            className="rounded-2xl border border-border/80 bg-white/90 p-5 shadow-lg shadow-indigo-100/40 backdrop-blur-sm dark:bg-card/90 dark:shadow-none"
          >
            <div className="flex flex-col gap-2.5 sm:flex-row">
              <Input
                type="file"
                name="file"
                accept=".pdf"
                disabled={isDisabled}
                className="h-11 rounded-xl border-border/70 bg-background shadow-sm sm:flex-1"
              />
              <Button
                type="submit"
                disabled={isDisabled}
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

            <GenerationSteps steps={steps} />

            {error === 'limit_exceeded' ? (
              <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-300">
                {isPaid ? (
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
        </div>
      </GenerationHero>
    </main>
  )
}
