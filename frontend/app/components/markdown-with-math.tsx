import type { ComponentProps } from 'react'
import ReactMarkdown from 'react-markdown'
import rehypeKatex from 'rehype-katex'
import remarkBreaks from 'remark-breaks'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'

import { cn } from '~/lib/utils'

import 'katex/dist/katex.min.css'

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
  img: ({ alt, className, ...props }) => {
    return (
      <img
        {...props}
        alt={alt ?? ''}
        loading="eager"
        decoding="async"
        className={cn(
          'my-2 max-h-[min(28rem,70vh)] w-auto max-w-full rounded-md object-contain',
          className,
        )}
      />
    )
  },
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
