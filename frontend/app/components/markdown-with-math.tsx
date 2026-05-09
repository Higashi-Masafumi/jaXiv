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
        <img
          {...props}
          alt={altText}
          loading="eager"
          decoding="async"
          className={cn(
            'my-2 max-h-[min(28rem,70vh)] w-auto max-w-full cursor-zoom-in rounded-md object-contain transition-opacity hover:opacity-90',
            className,
          )}
        />
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
        'prose prose-sm max-w-none break-words leading-relaxed dark:prose-invert',
        '[&_p:not(:last-child)]:mb-3 [&_li]:my-0.5 [&_ul]:my-2 [&_ol]:my-2',
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
