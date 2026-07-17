import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { ArrowRightIcon, FileUpIcon } from 'lucide-react'

import { useAuth } from '~/contexts/auth-context'
import { blogPostPath } from '~/lib/blog-path'
import { cn } from '~/lib/utils'
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
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)

  useEffect(() => {
    if (status === 'complete' && paperId) {
      navigate(blogPostPath(paperId, 'pdf'))
    }
  }, [status, paperId, navigate])

  // 選択した PDF の Blob URL を作り、iframe でプレビューする
  useEffect(() => {
    if (!file) {
      setPreviewUrl(null)
      return
    }
    const url = URL.createObjectURL(file)
    setPreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const isStreaming = status === 'streaming'
  const isDisabled = isStreaming || isAnonymous

  function selectFile(files: FileList | null) {
    const selected = files?.[0]
    if (!selected) return
    if (
      selected.type !== 'application/pdf' &&
      !selected.name.toLowerCase().endsWith('.pdf')
    )
      return
    setFile(selected)
  }

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
          <div className="rounded-2xl border border-border/80 bg-white/90 p-5 shadow-lg shadow-indigo-100/40 backdrop-blur-sm dark:bg-card/90 dark:shadow-none">
            {!file ? (
              <label
                onDragOver={e => {
                  e.preventDefault()
                  if (!isDisabled) setIsDragging(true)
                }}
                onDragLeave={e => {
                  e.preventDefault()
                  setIsDragging(false)
                }}
                onDrop={e => {
                  e.preventDefault()
                  setIsDragging(false)
                  if (!isDisabled) selectFile(e.dataTransfer.files)
                }}
                className={cn(
                  'flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-6 py-14 text-center transition-colors',
                  isDragging ? 'border-primary bg-primary/5' : 'border-border',
                  isDisabled && 'pointer-events-none opacity-60',
                )}
              >
                <FileUpIcon className="size-8 text-primary" />
                <div>
                  <p className="text-sm font-medium text-foreground">
                    ここに PDF をドラッグ＆ドロップ
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    またはクリックして選択（.pdf ファイル）
                  </p>
                </div>
                <Input
                  type="file"
                  accept=".pdf"
                  disabled={isDisabled}
                  className="hidden"
                  onChange={e => selectFile(e.target.files)}
                />
              </label>
            ) : (
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="truncate text-sm text-muted-foreground">
                    {file.name}
                  </p>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    disabled={isStreaming}
                    onClick={() => setFile(null)}
                  >
                    別の PDF を選択
                  </Button>
                </div>

                {previewUrl && (
                  <iframe
                    src={previewUrl}
                    title="PDF プレビュー"
                    className="h-[70vh] w-full rounded-xl border border-border bg-muted/30"
                  />
                )}

                <Button
                  type="button"
                  onClick={() => file && startPdfStream(file)}
                  disabled={isDisabled}
                  size="lg"
                  className="h-11 gap-1.5 rounded-xl px-6 font-semibold"
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
            )}

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
          </div>
        </div>
      </GenerationHero>
    </main>
  )
}
