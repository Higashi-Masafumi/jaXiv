import { useEffect, useRef, useState } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import { ChevronLeftIcon, ChevronRightIcon, FileTextIcon } from 'lucide-react'

import { Button } from './ui/button'

// pdf.js の worker を Vite 経由で解決する（react-pdf の Vite 向け推奨設定）
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString()

function PreviewMessage({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-64 flex-col items-center justify-center gap-2 text-sm text-muted-foreground">
      <FileTextIcon className="size-6 opacity-60" />
      {children}
    </div>
  )
}

/**
 * 選択された PDF ファイルをその場でプレビューする。
 * react-pdf(pdf.js) はブラウザ専用のため、このコンポーネントは
 * クライアントでのみ動的インポートして描画する。
 */
export function PdfPreview({ file }: { file: File }) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [numPages, setNumPages] = useState(0)
  const [pageNumber, setPageNumber] = useState(1)
  const [width, setWidth] = useState<number>()

  // ファイルが変わったら 1 ページ目に戻す
  useEffect(() => {
    setPageNumber(1)
    setNumPages(0)
  }, [file])

  // コンテナ幅に合わせてページ幅を追従させる
  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const observer = new ResizeObserver(entries => {
      const next = entries[0]?.contentRect.width
      if (next) setWidth(Math.floor(next))
    })
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  return (
    <div className="flex flex-col gap-3">
      <div
        ref={containerRef}
        className="max-h-[70vh] w-full overflow-y-auto rounded-xl border border-border/70 bg-muted/30 p-3"
      >
        <Document
          file={file}
          onLoadSuccess={info => setNumPages(info.numPages)}
          loading={<PreviewMessage>プレビューを読み込み中...</PreviewMessage>}
          error={
            <PreviewMessage>プレビューを表示できませんでした</PreviewMessage>
          }
          className="flex justify-center"
        >
          <Page
            pageNumber={pageNumber}
            width={width}
            renderAnnotationLayer={false}
            renderTextLayer={false}
            className="overflow-hidden rounded-md shadow-sm [&>canvas]:!h-auto [&>canvas]:!max-w-full"
          />
        </Document>
      </div>

      {numPages > 1 && (
        <div className="flex items-center justify-center gap-3">
          <Button
            type="button"
            variant="outline"
            size="icon"
            className="size-8"
            disabled={pageNumber <= 1}
            onClick={() => setPageNumber(p => Math.max(1, p - 1))}
            aria-label="前のページ"
          >
            <ChevronLeftIcon className="size-4" />
          </Button>
          <span className="text-xs tabular-nums text-muted-foreground">
            {pageNumber} / {numPages}
          </span>
          <Button
            type="button"
            variant="outline"
            size="icon"
            className="size-8"
            disabled={pageNumber >= numPages}
            onClick={() => setPageNumber(p => Math.min(numPages, p + 1))}
            aria-label="次のページ"
          >
            <ChevronRightIcon className="size-4" />
          </Button>
        </div>
      )}
    </div>
  )
}
