import { useChat } from '@ai-sdk/react'
import type { UIMessage } from 'ai'
import { DefaultChatTransport } from 'ai'
import { GlobeIcon, ImageIcon, Loader2Icon, SendIcon } from 'lucide-react'
import { useState } from 'react'

import { Button } from '~/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Input } from '~/components/ui/input'

function messageText(m: UIMessage): string {
  return m.parts
    .filter(
      (p): p is { type: 'text'; text: string } =>
        p.type === 'text' && 'text' in p && typeof p.text === 'string',
    )
    .map(p => p.text)
    .join('')
}

export function BlogPaperChat({ paperId }: { paperId: string }) {
  const [input, setInput] = useState('')
  const { messages, sendMessage, status } = useChat({
    transport: new DefaultChatTransport({
      api: `/blog/${encodeURIComponent(paperId)}`,
    }),
  })

  const busy = status === 'streaming' || status === 'submitted'

  return (
    <Card className="flex h-[min(80vh,720px)] flex-col border-border/80 shadow-sm">
      <CardHeader className="shrink-0 space-y-1 border-b pb-3">
        <CardTitle className="text-base font-semibold">アシスタント</CardTitle>
        <p className="text-muted-foreground text-xs leading-snug">
          この論文のインデックスに対して質問できます。検索はモデルが text /
          image ツールで実行します。
        </p>
      </CardHeader>
      <CardContent className="flex min-h-0 flex-1 flex-col gap-3 pt-4">
        <div className="min-h-0 flex-1 space-y-3 overflow-y-auto rounded-md border bg-muted/20 p-3 text-sm">
          {messages.length === 0 ? (
            <p className="text-muted-foreground">
              論文の内容について質問してください（ハイライト運用は今後対応）。
            </p>
          ) : (
            messages.map(m => (
              <div
                key={m.id}
                className={
                  m.role === 'user'
                    ? 'ml-4 rounded-lg bg-primary/10 px-3 py-2'
                    : 'mr-4 rounded-lg bg-background px-3 py-2 shadow-sm'
                }
              >
                <div className="text-muted-foreground mb-1 text-[10px] font-medium uppercase">
                  {m.role === 'user' ? 'あなた' : 'アシスタント'}
                </div>
                <div className="whitespace-pre-wrap break-words">
                  {messageText(m)}
                </div>
              </div>
            ))
          )}
          {busy && (
            <div className="text-muted-foreground flex items-center gap-2 text-xs">
              <Loader2Icon className="size-4 animate-spin" aria-hidden />
              考え中…
            </div>
          )}
        </div>
        <form
          className="shrink-0 space-y-2"
          onSubmit={e => {
            e.preventDefault()
            const t = input.trim()
            if (!t || busy) return
            void sendMessage({ text: t })
            setInput('')
          }}
        >
          <div className="relative">
            <Input
              placeholder="論文について質問…"
              value={input}
              onChange={e => setInput(e.target.value)}
              disabled={busy}
              className="pr-24"
              aria-label="チャット入力"
            />
            <div className="absolute top-1/2 right-2 flex -translate-y-1/2 items-center gap-1">
              <span
                className="text-muted-foreground inline-flex size-8 items-center justify-center rounded-md border border-dashed bg-muted/40"
                title="テキスト検索（モデルがツールで実行）"
              >
                <GlobeIcon className="size-3.5" aria-hidden />
              </span>
              <span
                className="text-muted-foreground inline-flex size-8 items-center justify-center rounded-md border border-dashed bg-muted/40"
                title="画像検索（モデルがツールで実行）"
              >
                <ImageIcon className="size-3.5" aria-hidden />
              </span>
              <Button
                type="submit"
                size="icon"
                variant="default"
                disabled={busy || !input.trim()}
                className="size-8 shrink-0"
                aria-label="送信"
              >
                <SendIcon className="size-4" />
              </Button>
            </div>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
