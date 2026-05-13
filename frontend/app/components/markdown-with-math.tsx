import type { ComponentProps } from 'react'
import ReactMarkdown from 'react-markdown'
import rehypeKatex from 'rehype-katex'
import remarkBreaks from 'remark-breaks'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from '~/components/ui/dialog'
import { cn } from '~/lib/utils'

import 'katex/dist/katex.min.css'

function ZoomableImage({ alt, className, ...props }: ComponentProps<'img'>) {
  const altText = alt ?? ''

  return (
    <Dialog>
      <DialogTrigger asChild>
        <button
          type="button"
          aria-label={altText ? `${altText}を拡大表示` : '画像を拡大表示'}
          className="my-2 inline-block cursor-zoom-in rounded-md bg-transparent p-0 transition-opacity hover:opacity-90 focus-visible:opacity-90 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:outline-none"
        >
          <img
            {...props}
            alt={altText}
            loading="eager"
            decoding="async"
            className={cn(
              'max-h-[min(28rem,70vh)] w-auto max-w-full rounded-md object-contain',
              className,
            )}
          />
        </button>
      </DialogTrigger>
      <DialogContent
        className="max-h-[95vh] w-auto max-w-[95vw] border-none bg-transparent p-0 shadow-none sm:max-w-[95vw]"
        showCloseButton
      >
        <DialogTitle className="sr-only">
          {altText || '画像のプレビュー'}
        </DialogTitle>
        <DialogDescription className="sr-only">
          {altText || '画像の拡大表示'}
        </DialogDescription>
        <img
          {...props}
          alt={altText}
          className="mx-auto max-h-[90vh] max-w-full rounded-md object-contain"
        />
        {altText && (
          <p className="mt-2 text-center text-sm text-white/90 drop-shadow">
            {altText}
          </p>
        )}
      </DialogContent>
    </Dialog>
  )
}

const markdownComponents: NonNullable<
  ComponentProps<typeof ReactMarkdown>['components']
> = {
  table: ({ children }) => (
    <div className="my-2 overflow-x-auto">
      <table className="w-full border-collapse text-xs">{children}</table>
    </div>
  ),
  th: ({ children }) => (
    <th className="border border-border bg-muted px-2 py-1 text-left font-semibold">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="border border-border px-2 py-1">{children}</td>
  ),
  img: ({ alt, className, ...props }) => (
    <ZoomableImage {...props} alt={alt} className={className} />
  ),
}

type MarkdownWithMathProps = {
  children: string
  className?: string
  /** ユーザー吹き出し（primary 背景）用の KaTeX 色 */
  variant?: 'default' | 'primary'
}

export function MarkdownWithMath({
  children,
  className,
  variant = 'default',
}: MarkdownWithMathProps) {
  return (
    <div
      className={cn(
        'prose prose-sm max-w-none break-words dark:prose-invert',
        // Tighten prose defaults for chat: 15px base, comfortable 1.7 line-height
        '[&_p]:text-[15px] [&_p]:leading-7 [&_li]:text-[15px] [&_li]:leading-7',
        '[&_p:not(:last-child)]:mb-3 [&_li]:my-1 [&_ul]:my-3 [&_ol]:my-3',
        '[&_code]:text-[13.5px] [&_pre]:text-[13px] [&_pre]:leading-6',
        '[&_h1]:mt-4 [&_h1]:mb-2 [&_h2]:mt-4 [&_h2]:mb-2 [&_h3]:mt-3 [&_h3]:mb-1.5',
        variant === 'default' && 'text-foreground',
        variant === 'primary' && [
          'prose-invert text-primary-foreground',
          '[&_.katex]:text-primary-foreground',
        ],
        className,
      )}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath, remarkBreaks]}
        rehypePlugins={[rehypeKatex]}
        components={markdownComponents}
      >
        {children}
      </ReactMarkdown>
    </div>
  )
}
