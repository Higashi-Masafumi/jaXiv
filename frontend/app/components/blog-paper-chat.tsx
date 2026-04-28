import {
  AlertCircleIcon,
  ArrowUpIcon,
  CheckIcon,
  ChevronRightIcon,
  HistoryIcon,
  Loader2Icon,
  PlusIcon,
  SearchIcon,
} from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router'

import { ChatThreadHistorySheet } from '~/components/chat-thread-history-sheet'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '~/components/ui/collapsible'
import { MarkdownWithMath } from '~/components/markdown-with-math'
import { Button } from '~/components/ui/button'
import { ScrollArea } from '~/components/ui/scroll-area'
import { Skeleton } from '~/components/ui/skeleton'
import { Textarea } from '~/components/ui/textarea'
import { cn } from '~/lib/utils'
import {
  type MessagePart,
  type PaperChatMessage,
  type ToolCallPart,
  usePaperChat,
} from '~/hooks/use-paper-chat'

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

function ToolCallResultSummary({ part }: { part: ToolCallPart }) {
  if (!part.result) return null
  const chunks =
    (part.result.chunks as { text: string; page_number: number }[]) ?? []
  const items =
    (part.result.items as {
      caption: string | null
      page_number: number
    }[]) ?? []

  if (chunks.length > 0) {
    return (
      <ul className="mt-1 space-y-1">
        {chunks.map((c, i) => (
          <li key={i} className="rounded bg-background/60 px-2 py-1">
            <span className="text-muted-foreground">p.{c.page_number}</span>{' '}
            {c.text.length > 120 ? `${c.text.slice(0, 120)}…` : c.text}
          </li>
        ))}
      </ul>
    )
  }
  if (items.length > 0) {
    return (
      <ul className="mt-1 space-y-1">
        {items.map((item, i) => (
          <li key={i} className="rounded bg-background/60 px-2 py-1">
            <span className="text-muted-foreground">p.{item.page_number}</span>{' '}
            {item.caption ?? '(no caption)'}
          </li>
        ))}
      </ul>
    )
  }
  return null
}

function ToolCallPartView({ part }: { part: ToolCallPart }) {
  const [open, setOpen] = useState(false)
  const query = (part.input.query as string) ?? ''

  const stateIcon =
    part.state === 'executing' ? (
      <Loader2Icon className="size-3 shrink-0 animate-spin" />
    ) : part.state === 'done' ? (
      <CheckIcon className="size-3 shrink-0 text-green-500" />
    ) : (
      <AlertCircleIcon className="size-3 shrink-0 text-red-500" />
    )

  const stateLabel =
    part.state === 'executing'
      ? '実行中…'
      : part.state === 'done'
        ? '完了'
        : 'エラー'

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger className="flex w-full items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors">
        <ChevronRightIcon
          className={cn(
            'size-3 shrink-0 transition-transform',
            open && 'rotate-90',
          )}
        />
        <SearchIcon className="size-3 shrink-0" />
        <span className="truncate">
          {part.name}
          {query && `: "${query}"`}
        </span>
        <span className="ml-auto flex items-center gap-1">
          {stateIcon}
          <span>{stateLabel}</span>
        </span>
      </CollapsibleTrigger>
      <CollapsibleContent className="mt-1 text-xs text-muted-foreground">
        <ToolCallResultSummary part={part} />
      </CollapsibleContent>
    </Collapsible>
  )
}

function MessagePartView({
  part,
  isUser,
}: {
  part: MessagePart
  isUser: boolean
}) {
  if (part.type === 'text') {
    return (
      <MarkdownWithMath variant={isUser ? 'primary' : 'default'}>
        {part.text}
      </MarkdownWithMath>
    )
  }
  if (part.type === 'tool-call') {
    return <ToolCallPartView part={part} />
  }
  return null
}

function MessageContent({ m }: { m: PaperChatMessage }) {
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
        {m.parts.map((part, i) => (
          <MessagePartView key={i} part={part} isUser={isUser} />
        ))}
      </div>
    </div>
  )
}

function HistoryLoadingSkeleton() {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex justify-end">
        <Skeleton className="h-9 w-2/3 rounded-lg" />
      </div>
      <div className="flex justify-start">
        <Skeleton className="h-16 w-3/4 rounded-lg" />
      </div>
      <div className="flex justify-end">
        <Skeleton className="h-9 w-1/2 rounded-lg" />
      </div>
    </div>
  )
}

export function BlogPaperChat({ paperId }: { paperId: string }) {
  const [input, setInput] = useState('')
  const [historyOpen, setHistoryOpen] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const [searchParams, setSearchParams] = useSearchParams()
  const threadId = searchParams.get('thread')

  const setThread = useCallback(
    (id: string | null, replace = false) => {
      setSearchParams(
        prev => {
          const next = new URLSearchParams(prev)
          if (id) next.set('thread', id)
          else next.delete('thread')
          return next
        },
        { replace },
      )
    },
    [setSearchParams],
  )

  const handleThreadCreated = useCallback(
    (id: string) => setThread(id, true),
    [setThread],
  )

  const handleThreadNotFound = useCallback(
    () => setThread(null, true),
    [setThread],
  )

  const { messages, sendMessage, status, error } = usePaperChat(paperId, {
    threadId,
    onThreadCreated: handleThreadCreated,
    onThreadNotFound: handleThreadNotFound,
  })

  const isLoadingHistory = status === 'loading'
  const isSubmitted = status === 'submitted'
  const busy = isSubmitted || status === 'streaming' || isLoadingHistory

  useEffect(() => {
    if (isLoadingHistory) return
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, status, isLoadingHistory])

  const submitChat = () => {
    const t = input.trim()
    if (!t || busy) return
    void sendMessage(t)
    setInput('')
  }

  return (
    <div className="flex h-full min-w-0 flex-col overflow-hidden bg-background">
      <div className="flex shrink-0 items-center justify-between gap-2 border-b border-border/40 px-3 py-2">
        <Button
          variant="ghost"
          size="sm"
          className="text-muted-foreground"
          disabled={!threadId || isSubmitted || status === 'streaming'}
          onClick={() => setThread(null)}
        >
          <PlusIcon />
          新しいチャット
        </Button>
        <Button
          variant="ghost"
          size="icon-sm"
          aria-label="チャット履歴"
          onClick={() => setHistoryOpen(true)}
        >
          <HistoryIcon />
        </Button>
      </div>

      {error && (
        <div className="flex shrink-0 items-start gap-2 border-b bg-destructive/10 px-4 py-2 text-xs text-destructive">
          <AlertCircleIcon className="mt-0.5 size-3.5 shrink-0" />
          <span className="break-all">{error.message}</span>
        </div>
      )}

      <ScrollArea className="min-h-0 flex-1">
        <div className="flex flex-col gap-3 px-4 py-4">
          {isLoadingHistory ? (
            <HistoryLoadingSkeleton />
          ) : messages.length === 0 && !busy ? (
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

      <ChatThreadHistorySheet
        paperId={paperId}
        currentThreadId={threadId}
        open={historyOpen}
        onOpenChange={setHistoryOpen}
        onSelect={id => setThread(id)}
      />
    </div>
  )
}
