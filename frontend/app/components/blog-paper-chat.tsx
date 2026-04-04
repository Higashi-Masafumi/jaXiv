import type { UIMessage } from 'ai'
import { DefaultChatTransport } from 'ai'
import { useChat } from '@ai-sdk/react'
import {
  AlertCircleIcon,
  CheckIcon,
  GlobeIcon,
  ImageIcon,
  Loader2Icon,
  SendIcon,
  WrenchIcon,
} from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { ScrollArea } from '~/components/ui/scroll-area'
import { cn } from '~/lib/utils'

const TOOL_LABEL: Record<string, string> = {
  textSearch: 'テキスト検索',
  imageSearch: '画像検索',
}

function ToolPart({ part }: { part: UIMessage['parts'][number] }) {
  const toolName = part.type.replace(/^tool-/, '')
  const label = TOOL_LABEL[toolName] ?? toolName
  const isDone = (part as { state?: string }).state === 'output-available'

  return (
    <div className="my-1 flex items-center gap-1.5 text-xs text-muted-foreground">
      {isDone ? (
        <CheckIcon className="size-3 shrink-0 text-green-500" />
      ) : (
        <WrenchIcon className="size-3 shrink-0 animate-pulse" />
      )}
      <span>
        {label}を{isDone ? '取得済み' : '検索中…'}
      </span>
    </div>
  )
}

function MessageContent({ m }: { m: UIMessage }) {
  const isUser = m.role === 'user'
  return (
    <div className={cn('flex', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={cn(
          'max-w-[85%] rounded-lg px-3 py-2 text-sm',
          isUser
            ? 'bg-primary text-primary-foreground'
            : 'bg-muted text-foreground',
        )}
      >
        {m.parts.map((part, i) => {
          if (part.type === 'text') {
            if (!part.text) return null
            if (isUser) {
              return (
                <p key={i} className="whitespace-pre-wrap break-words">
                  {part.text}
                </p>
              )
            }
            return (
              <div key={i} className="prose prose-sm dark:prose-invert max-w-none break-words">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    table: ({ children }) => (
                      <div className="overflow-x-auto my-2">
                        <table className="w-full border-collapse text-xs">{children}</table>
                      </div>
                    ),
                    th: ({ children }) => (
                      <th className="border border-border bg-muted px-2 py-1 text-left font-semibold">{children}</th>
                    ),
                    td: ({ children }) => (
                      <td className="border border-border px-2 py-1">{children}</td>
                    ),
                  }}
                >
                  {part.text}
                </ReactMarkdown>
              </div>
            )
          }
          if (part.type.startsWith('tool-')) {
            return <ToolPart key={i} part={part} />
          }
          return null
        })}
      </div>
    </div>
  )
}

export function BlogPaperChat({ paperId }: { paperId: string }) {
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  const { messages, sendMessage, status, error } = useChat({
    transport: new DefaultChatTransport({
      api: `/api/blog/${encodeURIComponent(paperId)}/chat`,
    }),
  })

  const isSubmitted = status === 'submitted'
  const busy = isSubmitted || status === 'streaming'

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, status])

  return (
    <div className="flex h-full flex-col bg-background">
      <div className="shrink-0 border-b px-4 py-3">
        <p className="text-sm font-semibold">アシスタント</p>
        <p className="mt-0.5 text-xs text-muted-foreground">
          text / image ツールで論文インデックスを検索します
        </p>
      </div>

      {error && (
        <div className="flex shrink-0 items-start gap-2 border-b bg-destructive/10 px-4 py-2 text-xs text-destructive">
          <AlertCircleIcon className="mt-0.5 size-3.5 shrink-0" />
          <span className="break-all">{error.message}</span>
        </div>
      )}

      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-3 p-4">
          {messages.length === 0 && !busy ? (
            <p className="text-sm text-muted-foreground">
              論文の内容について質問してください。
            </p>
          ) : (
            messages.map(m => <MessageContent key={m.id} m={m} />)
          )}

          {isSubmitted && (
            <div className="flex justify-start">
              <div className="flex items-center gap-1.5 rounded-lg bg-muted px-3 py-2 text-xs text-muted-foreground">
                <Loader2Icon className="size-3 animate-spin" />
                考え中…
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      <form
        className="shrink-0 border-t p-3"
        onSubmit={e => {
          e.preventDefault()
          const t = input.trim()
          if (!t || busy) return
          void sendMessage({ text: t })
          setInput('')
        }}
      >
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            <span
              className="inline-flex size-7 items-center justify-center rounded border border-dashed bg-muted/40 text-muted-foreground"
              title="テキスト検索（モデルがツールで実行）"
            >
              <GlobeIcon className="size-3" aria-hidden />
            </span>
            <span
              className="inline-flex size-7 items-center justify-center rounded border border-dashed bg-muted/40 text-muted-foreground"
              title="画像検索（モデルがツールで実行）"
            >
              <ImageIcon className="size-3" aria-hidden />
            </span>
          </div>
          <Input
            placeholder="論文について質問…"
            value={input}
            onChange={e => setInput(e.target.value)}
            disabled={busy}
            className="flex-1 text-sm"
            aria-label="チャット入力"
          />
          <Button
            type="submit"
            size="icon"
            disabled={busy || !input.trim()}
            className="size-8 shrink-0"
            aria-label="送信"
          >
            <SendIcon className="size-4" />
          </Button>
        </div>
      </form>
    </div>
  )
}
