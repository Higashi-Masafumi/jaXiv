import {
  AlertCircleIcon,
  MessageSquareIcon,
  MoreHorizontalIcon,
  PlusIcon,
  Trash2Icon,
} from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'

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
import { Button } from '~/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '~/components/ui/dropdown-menu'
import { ScrollArea } from '~/components/ui/scroll-area'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '~/components/ui/sheet'
import { Skeleton } from '~/components/ui/skeleton'
import {
  deleteChatThreadApiV1ChatThreadsThreadIdDelete,
  listChatThreadsApiV1ChatPaperPaperIdThreadsGet,
} from '~/api/sdk.gen'
import type { ChatThreadSummaryResponse } from '~/api/types.gen'
import { formatRelativeTime } from '~/lib/format-relative-time'
import { cn } from '~/lib/utils'

type Props = {
  paperId: string
  currentThreadId: string | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onSelect: (threadId: string | null) => void
}

function HistorySkeleton() {
  return (
    <div className="space-y-2 px-2">
      {[0, 1, 2].map(i => (
        <div key={i} className="space-y-2 rounded-md px-3 py-2">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/3" />
        </div>
      ))}
    </div>
  )
}

function ThreadRow(props: {
  thread: ChatThreadSummaryResponse
  isSelected: boolean
  onSelect: () => void
  onDelete: () => void
}) {
  const { thread, isSelected, onSelect, onDelete } = props
  return (
    <div
      className={cn(
        'group flex items-center gap-2 rounded-md px-3 py-2 transition-colors hover:bg-muted/50',
        isSelected && 'bg-accent/40',
      )}
    >
      <button
        type="button"
        onClick={onSelect}
        className="flex min-w-0 flex-1 flex-col gap-0.5 text-left"
      >
        <span className="truncate text-sm font-medium text-foreground">
          {thread.title}
        </span>
        <span className="text-xs text-muted-foreground">
          {formatRelativeTime(thread.updated_at)} ・ {thread.message_count} 件
        </span>
      </button>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="icon-sm"
            className="opacity-0 transition-opacity group-hover:opacity-100 data-[state=open]:opacity-100"
            aria-label="スレッドメニュー"
          >
            <MoreHorizontalIcon />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem variant="destructive" onSelect={onDelete}>
            <Trash2Icon />
            削除
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}

export function ChatThreadHistorySheet({
  paperId,
  currentThreadId,
  open,
  onOpenChange,
  onSelect,
}: Props) {
  const [threads, setThreads] = useState<ChatThreadSummaryResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [loadError, setLoadError] = useState<Error | null>(null)
  const [pendingDelete, setPendingDelete] =
    useState<ChatThreadSummaryResponse | null>(null)
  const [deleting, setDeleting] = useState(false)

  const refresh = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true)
      setLoadError(null)
      const { data, error } =
        await listChatThreadsApiV1ChatPaperPaperIdThreadsGet({
          path: { paper_id: paperId },
          signal,
          throwOnError: false,
        })
      if (signal?.aborted) return
      if (!data) {
        setLoadError(
          error instanceof Error
            ? error
            : new Error('スレッドの読み込みに失敗しました'),
        )
        setLoading(false)
        return
      }
      setThreads(data.threads)
      setLoading(false)
    },
    [paperId],
  )

  useEffect(() => {
    if (!open) return
    const ac = new AbortController()
    void refresh(ac.signal)
    return () => ac.abort()
  }, [open, refresh])

  const handleSelect = (threadId: string | null) => {
    onSelect(threadId)
    onOpenChange(false)
  }

  const handleDelete = async () => {
    if (!pendingDelete) return
    setDeleting(true)
    const target = pendingDelete
    const { error } = await deleteChatThreadApiV1ChatThreadsThreadIdDelete({
      path: { thread_id: target.id },
      throwOnError: false,
    })
    setDeleting(false)
    if (error) {
      setLoadError(
        error instanceof Error
          ? error
          : new Error('スレッドの削除に失敗しました'),
      )
      return
    }
    setThreads(prev => prev.filter(t => t.id !== target.id))
    setPendingDelete(null)
    if (currentThreadId === target.id) onSelect(null)
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex w-full flex-col sm:max-w-sm">
        <SheetHeader className="border-b">
          <SheetTitle>チャット履歴</SheetTitle>
          <SheetDescription>
            この論文の過去のチャットスレッドを開いたり削除できます。
          </SheetDescription>
        </SheetHeader>

        <div className="px-4">
          <Button
            variant="outline"
            size="sm"
            className="w-full justify-start"
            onClick={() => handleSelect(null)}
          >
            <PlusIcon />
            新しいチャット
          </Button>
        </div>

        {loadError && (
          <div className="mx-4 flex items-start gap-2 rounded-md bg-destructive/10 px-3 py-2 text-xs text-destructive">
            <AlertCircleIcon className="mt-0.5 size-3.5 shrink-0" />
            <span className="break-all">{loadError.message}</span>
          </div>
        )}

        <ScrollArea className="min-h-0 flex-1">
          <div className="px-2 pb-4">
            {loading ? (
              <HistorySkeleton />
            ) : threads.length === 0 ? (
              <div className="flex flex-col items-center gap-2 px-4 py-12 text-center text-sm text-muted-foreground">
                <MessageSquareIcon className="size-8 opacity-40" />
                <p>まだスレッドがありません</p>
              </div>
            ) : (
              <ul className="space-y-1">
                {threads.map(thread => (
                  <li key={thread.id}>
                    <ThreadRow
                      thread={thread}
                      isSelected={thread.id === currentThreadId}
                      onSelect={() => handleSelect(thread.id)}
                      onDelete={() => setPendingDelete(thread)}
                    />
                  </li>
                ))}
              </ul>
            )}
          </div>
        </ScrollArea>

        <AlertDialog
          open={pendingDelete !== null}
          onOpenChange={open => {
            if (!open) setPendingDelete(null)
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
      </SheetContent>
    </Sheet>
  )
}
