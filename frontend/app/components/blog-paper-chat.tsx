import type { DynamicToolUIPart, ToolUIPart, UIMessage } from 'ai'
import {
  DefaultChatTransport,
  getToolName,
  isToolUIPart,
  isTextUIPart,
} from 'ai'
import { useChat } from '@ai-sdk/react'
import {
  AlertCircleIcon,
  ArrowUpIcon,
  CheckIcon,
  Loader2Icon,
  WrenchIcon,
} from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { MarkdownWithMath } from '~/components/markdown-with-math'
import { Button } from '~/components/ui/button'
import { ScrollArea } from '~/components/ui/scroll-area'
import { Textarea } from '~/components/ui/textarea'
import { cn } from '~/lib/utils'

/** 下部固定の丸みのある入力（textarea + 円形送信） */
function ChatComposer(props: {
  value: string
  onChange: (v: string) => void
  disabled: boolean
  onSubmit: () => void
}) {
  const { value, onChange, disabled, onSubmit } = props

  return (
    <form
      className="pointer-events-auto mx-3 mb-3 mt-1"
      onSubmit={e => {
        e.preventDefault()
        onSubmit()
      }}
    >
      <div
        className={cn(
          'flex min-w-0 items-end gap-1.5 rounded-2xl border border-border/70 bg-muted/60 px-2 py-1.5',
          'shadow-md backdrop-blur-sm dark:bg-muted/40',
        )}
      >
        <Textarea
          placeholder="論文について質問…"
          value={value}
          onChange={e => onChange(e.target.value)}
          disabled={disabled}
          rows={1}
          aria-label="チャット入力（⌘+Enter または Ctrl+Enter で送信）"
          title="⌘+Enter（Windows は Ctrl+Enter）で送信"
          className={cn(
            'min-h-10 min-w-0 flex-1 resize-none text-sm leading-relaxed',
            'border-0 bg-transparent shadow-none',
            'outline-none focus-visible:border-transparent focus-visible:ring-0 focus-visible:outline-none',
            'max-h-36 py-2',
          )}
          onKeyDown={e => {
            if (e.key !== 'Enter') return
            if (!e.metaKey && !e.ctrlKey) return
            if (e.nativeEvent.isComposing) return
            e.preventDefault()
            onSubmit()
          }}
        />
        <Button
          type="submit"
          size="icon"
          disabled={disabled || !value.trim()}
          className="size-9 shrink-0 rounded-full"
          aria-label="送信"
        >
          <ArrowUpIcon className="size-4" strokeWidth={2.25} />
        </Button>
      </div>
    </form>
  )
}

function ToolPart({ part }: { part: ToolUIPart | DynamicToolUIPart }) {
  const toolName = getToolName(part)
  if (part.state === 'input-streaming') {
    return (
      <pre className="text-xs text-muted-foreground">
        {JSON.stringify(part.input, null, 2)}
      </pre>
    )
  }
  if (part.state === 'input-available') {
    return (
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <WrenchIcon className="size-3 shrink-0" />
        <span>{toolName}を実行中…</span>
      </div>
    )
  }
  if (part.state === 'output-available') {
    return (
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <CheckIcon className="size-3 shrink-0 text-green-500" />
        <span>{toolName}を実行完了</span>
      </div>
    )
  }
  if (part.state === 'output-error') {
    return (
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <AlertCircleIcon className="size-3 shrink-0 text-red-500" />
        <span>{toolName}を実行エラー</span>
      </div>
    )
  }
  return null
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
          if (isTextUIPart(part)) {
            return (
              <MarkdownWithMath
                key={i}
                variant={isUser ? 'primary' : 'default'}
              >
                {part.text}
              </MarkdownWithMath>
            )
          }
          if (isToolUIPart(part)) {
            return <ToolPart key={part.toolCallId} part={part} />
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

  const submitChat = () => {
    const t = input.trim()
    if (!t || busy) return
    void sendMessage({ text: t })
    setInput('')
  }

  return (
    <div className="flex h-full min-w-0 flex-col overflow-hidden bg-background">
      {error && (
        <div className="flex shrink-0 items-start gap-2 border-b bg-destructive/10 px-4 py-2 text-xs text-destructive">
          <AlertCircleIcon className="mt-0.5 size-3.5 shrink-0" />
          <span className="break-all">{error.message}</span>
        </div>
      )}

      <ScrollArea className="min-h-0 flex-1">
        <div className="flex flex-col gap-3 px-4 py-4">
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

      <div className="shrink-0 border-t border-border/40 bg-background/95 backdrop-blur-md">
        <ChatComposer
          value={input}
          onChange={setInput}
          disabled={busy}
          onSubmit={submitChat}
        />
      </div>
    </div>
  )
}
