import { Suspense, lazy, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { ArrowRightIcon, FileTextIcon, FileUpIcon, XIcon } from 'lucide-react'

import { useAuth } from '~/contexts/auth-context'
import { blogPostPath } from '~/lib/blog-path'
import { useBlogStream } from '../hooks/use-blog-stream'
import { GenerationHero } from '../components/generation-hero'
import { GenerationSteps } from '../components/generation-steps'
import { PdfDropzone } from '../components/pdf-dropzone'
import { Button } from '../components/ui/button'

// react-pdf(pdf.js) はブラウザ専用のため、クライアントでのみ動的に読み込む
const PdfPreview = lazy(() =>
  import('../components/pdf-preview').then(m => ({ default: m.PdfPreview })),
)

export function meta() {
  return [
    { title: 'PDFから作成 | jaXiv' },
    {
      name: 'description',
      content: 'PDF ファイルからブログ記事を生成します。',
    },
  ]
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function PreviewSkeleton() {
  return (
    <div className="flex h-64 items-center justify-center rounded-xl border border-border/70 bg-muted/30 text-sm text-muted-foreground">
      プレビューを準備中...
    </div>
  )
}

export default function Pdf() {
  const navigate = useNavigate()
  const { isAnonymous, isPaid } = useAuth()
  const { status, steps, error, paperId, startPdfStream } = useBlogStream()
  const [file, setFile] = useState<File | null>(null)
  // クライアントでのみ react-pdf を描画するためのマウント判定
  const [mounted, setMounted] = useState(false)

  useEffect(() => setMounted(true), [])

  useEffect(() => {
    if (status === 'complete' && paperId) {
      navigate(blogPostPath(paperId, 'pdf'))
    }
  }, [status, paperId, navigate])

  const isStreaming = status === 'streaming'
  const isDisabled = isStreaming || isAnonymous

  function handleGenerate() {
    if (file) startPdfStream(file)
  }

  return (
    <main className="h-full overflow-y-auto bg-background">
      <GenerationHero
        icon={FileUpIcon}
        badge="PDF をドラッグするだけでブログ記事に"
        titleLead="論文 PDF を、"
        titleHighlight="読みやすいブログに。"
        description="PDF ファイルをアップロードするだけで、AI が論文の内容を日本語ブログ記事に変換します。"
      >
        {isAnonymous && (
          <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-300">
            PDFからの生成には
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
              <PdfDropzone onSelect={setFile} disabled={isDisabled} />
            ) : (
              <div className="flex flex-col gap-4">
                <div className="flex items-center gap-3 rounded-xl border border-border/70 bg-muted/30 px-3.5 py-2.5">
                  <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                    <FileTextIcon className="size-4.5 text-primary" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-foreground">
                      {file.name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatFileSize(file.size)}
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="size-8 shrink-0 text-muted-foreground"
                    disabled={isStreaming}
                    onClick={() => setFile(null)}
                    aria-label="選択を解除"
                  >
                    <XIcon className="size-4" />
                  </Button>
                </div>

                {mounted ? (
                  <Suspense fallback={<PreviewSkeleton />}>
                    <PdfPreview file={file} />
                  </Suspense>
                ) : (
                  <PreviewSkeleton />
                )}

                <Button
                  type="button"
                  onClick={handleGenerate}
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
