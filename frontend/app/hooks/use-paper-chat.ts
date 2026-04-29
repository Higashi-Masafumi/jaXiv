import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router'
import {
  chatWithPaperApiV1ChatPaperPaperIdPost,
  getChatThreadApiV1ChatThreadsThreadIdGet,
} from '~/api/sdk.gen'
import type {
  ChatMessageResponse,
  TextBlock,
  ToolResultBlock,
  ToolUseBlock,
} from '~/api/types.gen'
import { supabase } from '~/lib/supabase'

export type ChatStatus = 'idle' | 'loading' | 'submitted' | 'streaming'

export type PaperChatMessage = ChatMessageResponse

// SSE event shapes — mirror application/chat_events.py
type ChatStreamEvent =
  | { type: 'thread_id'; thread_id: string }
  | { type: 'message_start'; message_id: string; role: 'user' | 'assistant' }
  | {
      type: 'block_start'
      index: number
      block: TextBlock | ToolUseBlock | ToolResultBlock
    }
  | {
      type: 'block_delta'
      index: number
      delta: { type: 'text_delta'; text: string }
    }
  | { type: 'block_stop'; index: number }
  | { type: 'message_stop' }
  | { type: 'error'; message: string }

export type UsePaperChatOptions = {
  initialThreadId?: string | null
  onThreadCreated?: (threadId: string) => void
}

export function usePaperChat(
  paperId: string,
  options: UsePaperChatOptions = {},
) {
  const { initialThreadId, onThreadCreated } = options
  const [messages, setMessages] = useState<PaperChatMessage[]>([])
  const [status, setStatus] = useState<ChatStatus>(
    initialThreadId ? 'loading' : 'idle',
  )
  const [error, setError] = useState<Error | null>(null)
  const threadIdRef = useRef<string | null>(initialThreadId ?? null)
  const navigate = useNavigate()

  // 既存スレッド再開時は履歴を fetch して messages に流し込む。
  useEffect(() => {
    if (!initialThreadId) return
    const ac = new AbortController()
    setStatus('loading')
    setError(null)
    void (async () => {
      const { data, error: apiError } =
        await getChatThreadApiV1ChatThreadsThreadIdGet({
          path: { thread_id: initialThreadId },
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
        setStatus('idle')
        return
      }
      setMessages(data.messages ?? [])
      setStatus('idle')
    })()
    return () => ac.abort()
  }, [initialThreadId])

  const sendMessage = useCallback(
    async (text: string) => {
      if (status !== 'idle') return

      const {
        data: { session },
      } = await supabase.auth.getSession()
      if (!session || session.user.is_anonymous) {
        void navigate('/login')
        return
      }

      const userMessageId = crypto.randomUUID()
      setMessages(prev => [
        ...prev,
        {
          id: userMessageId,
          role: 'user',
          content: [{ type: 'text', text }],
          timestamp: new Date().toISOString(),
        },
      ])
      setStatus('submitted')
      setError(null)

      let currentMessageId: string | null = null

      const upsertMessage = (
        id: string,
        role: 'user' | 'assistant',
        updater: (m: PaperChatMessage) => PaperChatMessage,
      ) => {
        setMessages(prev => {
          const idx = prev.findIndex(m => m.id === id)
          if (idx >= 0) {
            const next = [...prev]
            next[idx] = updater(next[idx]!)
            return next
          }
          const blank: PaperChatMessage = {
            id,
            role,
            content: [],
            timestamp: new Date().toISOString(),
          }
          return [...prev, updater(blank)]
        })
      }

      const applyEvent = (event: ChatStreamEvent) => {
        switch (event.type) {
          case 'thread_id': {
            if (event.thread_id !== threadIdRef.current) {
              threadIdRef.current = event.thread_id
              onThreadCreated?.(event.thread_id)
            }
            break
          }
          case 'message_start': {
            currentMessageId = event.message_id
            upsertMessage(event.message_id, event.role, m => m)
            break
          }
          case 'block_start': {
            if (!currentMessageId) break
            const block = event.block
            upsertMessage(currentMessageId, 'assistant', m => ({
              ...m,
              content: [...m.content, block],
            }))
            break
          }
          case 'block_delta': {
            if (!currentMessageId) break
            upsertMessage(currentMessageId, 'assistant', m => {
              const content = [...m.content]
              for (let i = content.length - 1; i >= 0; i -= 1) {
                const b = content[i]
                if (b && b.type === 'text') {
                  content[i] = { ...b, text: b.text + event.delta.text }
                  break
                }
              }
              return { ...m, content }
            })
            break
          }
          case 'block_stop':
          case 'message_stop':
            break
          case 'error':
            setError(new Error(event.message))
            break
        }
      }

      try {
        const { stream } = await chatWithPaperApiV1ChatPaperPaperIdPost({
          path: { paper_id: paperId },
          body: { message: text, thread_id: threadIdRef.current },
        })
        setStatus('streaming')
        for await (const raw of stream) {
          applyEvent(raw as ChatStreamEvent)
        }
      } catch (e) {
        setError(e instanceof Error ? e : new Error(String(e)))
      } finally {
        setStatus('idle')
      }
    },
    [paperId, status, onThreadCreated, navigate],
  )

  return { messages, status, error, sendMessage }
}
