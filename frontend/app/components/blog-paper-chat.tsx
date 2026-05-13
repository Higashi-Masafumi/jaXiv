import {
  AlertCircleIcon,
  ArrowLeftIcon,
  ArrowUpIcon,
  CheckIcon,
  ChevronRightIcon,
  HistoryIcon,
  Loader2Icon,
  MessageSquareIcon,
  PlusIcon,
  SearchIcon,
  SquareIcon,
  Trash2Icon,
} from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router'

import { useAuth } from '~/contexts/auth-context'

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '~/components/ui/alert-dialog'
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
import {
  deleteChatThreadApiV1ChatThreadsThreadIdDelete,
  listChatThreadsApiV1ChatPaperPaperIdThreadsGet,
} from '~/api/sdk.gen'
import type {
  ChatThreadSummaryResponse,
  ToolResultBlock,
  ToolUseBlock,
} from '~/api/types.gen'
import { cn } from '~/lib/utils'
import { type PaperChatMessage, usePaperChat } from '~/hooks/use-paper-chat'

const dateFormatter = new Intl.DateTimeFormat('ja-JP', { dateStyle: 'short' })

function ChatComposer(props: {
  value: string
  onChange: (v: string) => void
  busy: boolean
  disabled: boolean
  onSubmit: () => void
}) {
  const { value, onChange, busy, disabled, onSubmit } = props
  const canSubmit = !busy && !disabled && value.trim().length > 0

  return (
    <form
      className="pointer-events-auto mx-3 mb-3 mt-1"
      onSubmit={e => {
        e.preventDefault()
        if (!canSubmit) return
        onSubmit()
      }}
    >
      <div
        className={cn(
          'flex min-w-0 items-end gap-1.5 rounded-2xl border border-chat-composer-border bg-chat-composer-surface px-2 py-1.5',
          'shadow-sm backdrop-blur-sm transition-shadow',
          'focus-within:border-ring/60 focus-within:shadow-md',
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
            'min-h-10 min-w-0 flex-1 resize-none text-[15px] leading-6 text-foreground placeholder:text-muted-foreground/80',
            'border-0 bg-transparent shadow-none',
            'outline-none focus-visible:border-transparent focus-visible:ring-0 focus-visible:outline-none',
            'max-h-40 py-2',
          )}
          onKeyDown={e => {
            if (e.key !== 'Enter') return
            if (!e.metaKey && !e.ctrlKey) return
            if (e.nativeEvent.isComposing) return
            e.preventDefault()
            if (!canSubmit) return
            onSubmit()
          }}
        />
        <Button
          type="submit"
          size="icon"
          disabled={!canSubmit}
          className="size-9 shrink-0 rounded-full"
          aria-label={busy ? '生成中' : '送信'}
          title={busy ? '生成中…' : '送信 (⌘+Enter)'}
        >
          {busy ? (
            <SquareIcon className="size-3.5 fill-current" strokeWidth={0} />
          ) : (
            <ArrowUpIcon className="size-4" strokeWidth={2.25} />
          )}
        </Button>
      </div>
    </form>
  )
}

type ToolUseState = 'executing' | 'done' | 'error'

function ToolResultSummary({ result }: { result: ToolResultBlock }) {
  const content = (result.content ?? {}) as Record<string, unknown>
  const chunks =
    (content.chunks as { text: string; page_number: number }[] | undefined) ??
    []
  const items =
    (content.items as
      | { caption: string | null; page_number: number }[]
      | undefined) ?? []

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

function ToolUseView({
  block,
  result,
  state,
}: {
  block: ToolUseBlock
  result: ToolResultBlock | null
  state: ToolUseState
}) {
  const [open, setOpen] = useState(false)
  const query = (block.input?.query as string | undefined) ?? ''

  const stateIcon =
    state === 'executing' ? (
      <Loader2Icon className="size-3 shrink-0 animate-spin" />
    ) : state === 'done' ? (
      <CheckIcon className="size-3 shrink-0 text-green-500" />
    ) : (
      <AlertCircleIcon className="size-3 shrink-0 text-red-500" />
    )

  const stateLabel =
    state === 'executing' ? '実行中…' : state === 'done' ? '完了' : 'エラー'

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
          {block.name}
          {query && `: "${query}"`}
        </span>
        <span className="ml-auto flex items-center gap-1">
          {stateIcon}
          <span>{stateLabel}</span>
        </span>
      </CollapsibleTrigger>
      <CollapsibleContent className="mt-1 text-xs text-muted-foreground">
        {result && <ToolResultSummary result={result} />}
      </CollapsibleContent>
    </Collapsible>
  )
}

type ResolvedToolUse = {
  block: ToolUseBlock
  result: ToolResultBlock | null
  state: ToolUseState
}

function buildToolResultIndex(
  messages: PaperChatMessage[],
): Map<string, ToolResultBlock> {
  const index = new Map<string, ToolResultBlock>()
  for (const m of messages) {
    if (m.role !== 'user') continue
    for (const block of m.content) {
      if (block.type === 'tool_result') {
        index.set(block.tool_use_id, block)
      }
    }
  }
  return index
}

function AssistantMessage({
  message,
  toolResults,
}: {
  message: PaperChatMessage
  toolResults: Map<string, ToolResultBlock>
}) {
  return (
    <div className="flex justify-start">
      <div
        className={cn(
          'max-w-[88%] rounded-2xl border border-chat-assistant-border bg-chat-assistant-surface text-chat-assistant-foreground',
          'px-4 py-3 text-[15px] leading-7 shadow-[0_1px_2px_rgb(0_0_0/0.02)]',
        )}
      >
        {message.content.map((block, i) => {
          if (block.type === 'text') {
            return (
              <MarkdownWithMath key={i} variant="default">
                {block.text}
              </MarkdownWithMath>
            )
          }
          if (block.type === 'tool_use') {
            const result = toolResults.get(block.id) ?? null
            const tu: ResolvedToolUse = {
              block,
              result,
              state: result
                ? result.is_error
                  ? 'error'
                  : 'done'
                : 'executing',
            }
            return (
              <ToolUseView
                key={i}
                block={tu.block}
                result={tu.result}
                state={tu.state}
              />
            )
          }
          return null
        })}
      </div>
    </div>
  )
}

function UserMessage({ message }: { message: PaperChatMessage }) {
  // user メッセージのうち tool_result-only のものはアシスタント側に
  // 折りたたまれて表示されるので、ユーザーバブルとしては描画しない。
  const textBlocks = message.content.filter(b => b.type === 'text')
  if (textBlocks.length === 0) return null
  return (
    <div className="flex justify-end">
      <div
        className={cn(
          'max-w-[80%] rounded-2xl bg-chat-user-surface text-chat-user-foreground',
          'px-4 py-2.5 text-[15px] leading-6 shadow-sm',
        )}
      >
        {textBlocks.map((block, i) => (
          <MarkdownWithMath key={i} variant="primary">
            {block.text}
          </MarkdownWithMath>
        ))}
      </div>
    </div>
  )
}

function ThreadListView(props: {
  paperId: string
  currentThreadId: string | null
  onSelect: (id: string) => void
}) {
  const { paperId, currentThreadId, onSelect } = props
  const [threads, setThreads] = useState<ChatThreadSummaryResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [pendingDelete, setPendingDelete] =
    useState<ChatThreadSummaryResponse | null>(null)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    const ac = new AbortController()
    setLoading(true)
    setError(null)
    void (async () => {
      const { data, error: apiError } =
        await listChatThreadsApiV1ChatPaperPaperIdThreadsGet({
          path: { paper_id: paperId },
          signal: ac.signal,
          throwOnError: false,
        })
      if (ac.signal.aborted) return
      if (!data) {
        setError(
          apiError instanceof Error
            ? apiError
            : new Error('スレッドの読み込みに失敗しました'),
        )
        setLoading(false)
        return
      }
      setThreads(data.threads)
      setLoading(false)
    })()
    return () => ac.abort()
  }, [paperId])

  const handleDelete = async () => {
    if (!pendingDelete) return
    setDeleting(true)
    const target = pendingDelete
    const { error: apiError } =
      await deleteChatThreadApiV1ChatThreadsThreadIdDelete({
        path: { thread_id: target.id },
        throwOnError: false,
      })
    setDeleting(false)
    if (apiError) {
      setError(
        apiError instanceof Error
          ? apiError
          : new Error('スレッドの削除に失敗しました'),
      )
      return
    }
    setThreads(prev => prev.filter(t => t.id !== target.id))
    setPendingDelete(null)
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <ScrollArea className="min-h-0 flex-1">
        <div className="px-2 py-2">
          {error && (
            <div className="mx-2 mb-2 flex items-start gap-2 rounded-md bg-destructive/10 px-3 py-2 text-xs text-destructive">
              <AlertCircleIcon className="mt-0.5 size-3.5 shrink-0" />
              <span className="break-all">{error.message}</span>
            </div>
          )}

          {loading ? (
            <div className="space-y-2 px-2">
              <div className="space-y-2 rounded-md px-3 py-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/3" />
              </div>
              <div className="space-y-2 rounded-md px-3 py-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/3" />
              </div>
              <div className="space-y-2 rounded-md px-3 py-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/3" />
              </div>
            </div>
          ) : threads.length === 0 ? (
            <div className="flex flex-col items-center gap-2 px-4 py-12 text-center text-sm text-muted-foreground">
              <MessageSquareIcon className="size-8 opacity-40" />
              <p>まだスレッドがありません</p>
            </div>
          ) : (
            <ul className="grid grid-cols-[minmax(0,1fr)] gap-1">
              {threads.map(thread => (
                <li
                  key={thread.id}
                  className={cn(
                    'group grid grid-cols-[minmax(0,1fr)_auto] items-center gap-2 rounded-md px-3 py-2 transition-colors hover:bg-muted/50',
                    thread.id === currentThreadId && 'bg-accent/40',
                  )}
                >
                  <button
                    type="button"
                    onClick={() => onSelect(thread.id)}
                    className="flex min-w-0 flex-col gap-0.5 text-left"
                  >
                    <span className="truncate text-sm font-medium text-foreground">
                      {thread.title}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {dateFormatter.format(new Date(thread.updated_at))}
                    </span>
                  </button>
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    aria-label="このスレッドを削除"
                    className="text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100 focus-visible:opacity-100 hover:text-destructive"
                    onClick={() => setPendingDelete(thread)}
                  >
                    <Trash2Icon />
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </ScrollArea>

      <AlertDialog
        open={pendingDelete !== null}
        onOpenChange={isOpen => {
          if (!isOpen) setPendingDelete(null)
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>このスレッドを削除しますか?</AlertDialogTitle>
            <AlertDialogDescription>
              「{pendingDelete?.title}
              」のメッセージはすべて削除され、元に戻せません。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>
              キャンセル
            </AlertDialogCancel>
            <AlertDialogAction
              disabled={deleting}
              onClick={e => {
                e.preventDefault()
                void handleDelete()
              }}
              className="bg-destructive text-white hover:bg-destructive/90 focus-visible:ring-destructive/20"
            >
              {deleting ? '削除中…' : '削除'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

function ChatLimitAlert() {
  const { isPaid } = useAuth()
  return (
    <div className="flex shrink-0 items-start gap-2 border-b border-hero-accent/40 bg-hero-accent/10 px-4 py-2 text-xs">
      <AlertCircleIcon className="mt-0.5 size-3.5 shrink-0 text-hero-accent" />
      <span className="break-all">
        {isPaid ? (
          <>
            本日のチャット利用が上限に達しました。日付が変わるとリセットされます。
          </>
        ) : (
          <>
            本日のチャット上限（30 メッセージ）に達しました。
            <Link
              to="/pricing"
              className="ml-1 font-semibold underline underline-offset-2"
            >
              有料プランにアップグレード
            </Link>
            すると無制限で利用できます。
          </>
        )}
      </span>
    </div>
  )
}

function ChatView(props: {
  paperId: string
  initialThreadId: string | null
  onThreadCreated: (id: string) => void
}) {
  const { paperId, initialThreadId, onThreadCreated } = props
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  const { messages, sendMessage, status, error } = usePaperChat(paperId, {
    initialThreadId,
    onThreadCreated,
  })

  const isLoading = status === 'loading'
  const isSubmitted = status === 'submitted'
  const busy = isLoading || isSubmitted || status === 'streaming'

  const toolResults = useMemo(() => buildToolResultIndex(messages), [messages])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, status])

  const submitChat = () => {
    const t = input.trim()
    if (!t || busy) return
    void sendMessage(t)
    setInput('')
  }

  return (
    <>
      {error?.code === 'chat_limit_exceeded' ? (
        <ChatLimitAlert />
      ) : (
        error && (
          <div className="flex shrink-0 items-start gap-2 border-b bg-destructive/10 px-4 py-2 text-xs text-destructive">
            <AlertCircleIcon className="mt-0.5 size-3.5 shrink-0" />
            <span className="break-all">{error.message}</span>
          </div>
        )
      )}

      <ScrollArea className="min-h-0 flex-1">
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-5 px-4 py-6">
          {isLoading ? (
            <div className="space-y-5">
              <div className="flex justify-end">
                <Skeleton className="h-14 w-2/3 rounded-2xl" />
              </div>
              <div className="flex justify-start">
                <Skeleton className="h-20 w-3/4 rounded-2xl" />
              </div>
            </div>
          ) : messages.length === 0 && !busy ? (
            <p className="text-[15px] leading-7 text-muted-foreground">
              論文の内容について質問してください。
            </p>
          ) : (
            messages.map(m =>
              m.role === 'assistant' ? (
                <AssistantMessage
                  key={m.id}
                  message={m}
                  toolResults={toolResults}
                />
              ) : (
                <UserMessage key={m.id} message={m} />
              ),
            )
          )}

          {isSubmitted && (
            <div className="flex justify-start">
              <div className="flex items-center gap-2 rounded-2xl border border-chat-assistant-border bg-chat-assistant-surface px-4 py-2.5 text-sm text-muted-foreground">
                <Loader2Icon className="size-3.5 animate-spin" />
                考え中…
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      <div className="shrink-0 border-t border-border/40 bg-background/95 backdrop-blur-md">
        <div className="mx-auto w-full max-w-3xl">
          <ChatComposer
            value={input}
            onChange={setInput}
            busy={busy}
            disabled={error?.code === 'chat_limit_exceeded'}
            onSubmit={submitChat}
          />
        </div>
      </div>
    </>
  )
}

export function BlogPaperChat({ paperId }: { paperId: string }) {
  const [view, setView] = useState<'chat' | 'history'>('chat')
  const [searchParams, setSearchParams] = useSearchParams()
  // URL はブックマーク・共有用に同期するが、ChatView への受け渡しには
  // ローカル state を使う。setSearchParams は非同期で反映されるため、
  // 同一レンダー内で setChatKey と組み合わせると古い値が渡される問題を防ぐ。
  const [threadId, setThreadId] = useState<string | null>(
    searchParams.get('thread'),
  )
  const [chatKey, setChatKey] = useState(0)

  const setThread = useCallback(
    (id: string | null, replace = false) => {
      setThreadId(id)
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

  const startNewChat = () => {
    setThread(null)
    setView('chat')
    setChatKey(k => k + 1)
  }

  const selectThread = (id: string) => {
    setThread(id)
    setView('chat')
    setChatKey(k => k + 1)
  }

  return (
    <div className="flex h-full min-w-0 flex-col overflow-hidden bg-background">
      <div className="flex shrink-0 items-center justify-between gap-2 border-b border-border/40 px-3 py-2">
        {view === 'chat' ? (
          <>
            <span className="text-sm font-medium text-foreground">
              アシスタント
            </span>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                className="text-muted-foreground"
                disabled={!threadId}
                onClick={startNewChat}
              >
                <PlusIcon />
                新しいチャット
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="text-muted-foreground"
                onClick={() => setView('history')}
              >
                <HistoryIcon />
                履歴
              </Button>
            </div>
          </>
        ) : (
          <>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon-sm"
                aria-label="チャットに戻る"
                onClick={() => setView('chat')}
              >
                <ArrowLeftIcon />
              </Button>
              <span className="text-sm font-medium text-foreground">
                チャット履歴
              </span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="text-muted-foreground"
              onClick={startNewChat}
            >
              <PlusIcon />
              新しいチャット
            </Button>
          </>
        )}
      </div>

      {view === 'history' ? (
        <ThreadListView
          paperId={paperId}
          currentThreadId={threadId}
          onSelect={selectThread}
        />
      ) : (
        <ChatView
          key={chatKey}
          paperId={paperId}
          initialThreadId={threadId}
          onThreadCreated={handleThreadCreated}
        />
      )}
    </div>
  )
}
