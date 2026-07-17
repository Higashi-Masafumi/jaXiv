import { useRef, useState } from 'react'
import { FileUpIcon } from 'lucide-react'

import { cn } from '~/lib/utils'

function isPdf(file: File) {
  return (
    file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
  )
}

/**
 * PDF をドラッグ＆ドロップ、またはクリックで選択するためのゾーン。
 * 追加ライブラリを使わずネイティブの drag/drop イベントで実装する。
 */
export function PdfDropzone({
  onSelect,
  disabled,
}: {
  onSelect: (file: File) => void
  disabled?: boolean
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)

  function handleFiles(files: FileList | null) {
    const file = files?.[0]
    if (!file || !isPdf(file)) return
    onSelect(file)
  }

  function openPicker() {
    if (!disabled) inputRef.current?.click()
  }

  return (
    <div
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-disabled={disabled}
      aria-label="PDF を選択"
      onClick={openPicker}
      onKeyDown={e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          openPicker()
        }
      }}
      onDragOver={e => {
        e.preventDefault()
        if (!disabled) setIsDragging(true)
      }}
      onDragLeave={e => {
        e.preventDefault()
        setIsDragging(false)
      }}
      onDrop={e => {
        e.preventDefault()
        setIsDragging(false)
        if (!disabled) handleFiles(e.dataTransfer.files)
      }}
      className={cn(
        'flex flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed px-6 py-14 text-center transition-colors outline-none',
        'focus-visible:border-primary focus-visible:ring-[3px] focus-visible:ring-ring/50',
        isDragging
          ? 'border-primary bg-primary/5'
          : 'border-border/70 bg-white/60 dark:bg-card/60',
        disabled
          ? 'cursor-not-allowed opacity-60'
          : 'cursor-pointer hover:border-primary/50 hover:bg-primary/5',
      )}
    >
      <div
        className={cn(
          'flex size-12 items-center justify-center rounded-full transition-colors',
          isDragging ? 'bg-primary/15' : 'bg-primary/8',
        )}
      >
        <FileUpIcon className="size-6 text-primary" />
      </div>
      <div>
        <p className="text-sm font-semibold text-foreground">
          ここに PDF をドラッグ＆ドロップ
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          または
          <span className="font-medium text-primary">クリックして選択</span>
          （.pdf ファイル）
        </p>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,application/pdf"
        className="hidden"
        disabled={disabled}
        onChange={e => {
          handleFiles(e.target.files)
          e.target.value = ''
        }}
      />
    </div>
  )
}
