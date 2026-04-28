import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router'
import {
  chatWithPaperApiV1ChatPaperPaperIdPost,
  getChatThreadApiV1ChatThreadsThreadIdGet,
} from '~/api/sdk.gen'
import { historyToMessages } from '~/lib/chat-messages'
import { supabase } from '~/lib/supabase'

export type TextPart = { type: 'text'; text: string }
export type ToolCallPart = {
  type: 'tool-call'
  toolCallId: string
  name: string
  input: Record<string, unknown>
  result: Record<string, unknown> | null
  state: 'executing' | 'done' | 'error'
}
export type MessagePart = TextPart | ToolCallPart

export type PaperChatMessage = {
  id: string
  role: 'user' | 'assistant'
  parts: MessagePart[]
}

// SSE event shapes — mirrors application/chat_events.py (response is `unknown` in OpenAPI schema)
type ChatStreamEvent =
  | { type: 'thread_id'; thread_id: string }
  | { type: 'block_start'; index: number; block: { type: 'text' } }
  | {
      type: 'block_start'
      index: number
      block: {
        type: 'tool_use'
        id: string
        name: string
        input: Record<string, unknown>
      }
    }
  | {
      type: 'block_delta'
      index: number
      delta: { type: 'text_delta'; text: string }
    }
  | {
      type: 'tool_result'
      tool_use_id: string
      name: string
      content: Record<string, unknown>
    }
  | { type: 'error'; message: string }

export type ChatStatus = 'idle' | 'loading' | 'submitted' | 'streaming'

export type UsePaperChatOptions = {
  threadId: string | null
  onThreadCreated?: (threadId: string) => void
  onThreadNotFound?: () => void
}

export function usePaperChat(paperId: string, options: UsePaperChatOptions) {
  const { threadId, onThreadCreated, onThreadNotFound } = options
  const [messages, setMessages] = useState<PaperChatMessage[]>([])
  const [status, setStatus] = useState<ChatStatus>('idle')
  const [error, setError] = useState<Error | null>(null)
  const threadIdRef = useRef<string | null>(threadId)
  const abortRef = useRef<AbortController | null>(null)
  const navigate = useNavigate()

  const onThreadCreatedRef = useRef(onThreadCreated)
  const onThreadNotFoundRef = useRef(onThreadNotFound)
  useEffect(() => {
    onThreadCreatedRef.current = onThreadCreated
    onThreadNotFoundRef.current = onThreadNotFound
  }, [onThreadCreated, onThreadNotFound])

  useEffect(() => {
    threadIdRef.current = threadId
    if (!threadId) {
      setMessages([])
      setError(null)
      return
    }

    const ac = new AbortController()
    setStatus('loading')
    setError(null)
    void (async () => {
      const { data, error: apiError } =
        await getChatThreadApiV1ChatThreadsThreadIdGet({
          path: { thread_id: threadId },
          signal: ac.signal,
          throwOnError: false,
        })
      if (ac.signal.aborted) return
      if (!data) {
        if (apiError && typeof apiError === 'object' && 'detail' in apiError) {
          setError(new Error(String((apiError as { detail: unknown }).detail)))
        } else {
          setError(new Error('スレッドの読み込みに失敗しました'))
        }
        setMessages([])
        setStatus('idle')
        onThreadNotFoundRef.current?.()
        return
      }
      setMessages(historyToMessages(data.messages))
      setStatus('idle')
    })()

    return () => ac.abort()
  }, [threadId])

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

      const assistantId = crypto.randomUUID()
      setMessages(prev => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'user',
          parts: [{ type: 'text', text }],
        },
        { id: assistantId, role: 'assistant', parts: [] },
      ])
      setStatus('submitted')
      setError(null)

      const abort = new AbortController()
      abortRef.current = abort

      const updateAssistant = (
        updater: (m: PaperChatMessage) => PaperChatMessage,
      ) =>
        setMessages(prev =>
          prev.map(m => (m.id === assistantId ? updater(m) : m)),
        )

      const applyEvent = (event: ChatStreamEvent) => {
        switch (event.type) {
          case 'thread_id': {
            const isNew = threadIdRef.current !== event.thread_id
            threadIdRef.current = event.thread_id
            if (isNew) onThreadCreatedRef.current?.(event.thread_id)
            break
          }
          case 'block_start': {
            const part: MessagePart =
              event.block.type === 'text'
                ? { type: 'text', text: '' }
                : {
                    type: 'tool-call',
                    toolCallId: event.block.id,
                    name: event.block.name,
                    input: event.block.input,
                    result: null,
                    state: 'executing',
                  }
            updateAssistant(m => ({ ...m, parts: [...m.parts, part] }))
            break
          }
          case 'block_delta':
            updateAssistant(m => {
              const parts = [...m.parts]
              let idx = -1
              for (let i = parts.length - 1; i >= 0; i -= 1) {
                if (parts[i]?.type === 'text') {
                  idx = i
                  break
                }
              }
              if (idx >= 0)
                parts[idx] = {
                  type: 'text',
                  text: (parts[idx] as TextPart).text + event.delta.text,
                }
              return { ...m, parts }
            })
            break
          case 'tool_result':
            updateAssistant(m => ({
              ...m,
              parts: m.parts.map(p =>
                p.type === 'tool-call' && p.toolCallId === event.tool_use_id
                  ? { ...p, state: 'done' as const, result: event.content }
                  : p,
              ),
            }))
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
          signal: abort.signal,
        })
        setStatus('streaming')
        for await (const raw of stream) {
          applyEvent(raw as ChatStreamEvent)
        }
      } catch (e) {
        if (e instanceof Error && e.name === 'AbortError') return
        setError(e instanceof Error ? e : new Error(String(e)))
        setMessages(prev =>
          prev.filter(m => !(m.id === assistantId && m.parts.length === 0)),
        )
      } finally {
        setStatus('idle')
        abortRef.current = null
      }
    },
    [paperId, status, navigate],
  )

  const stop = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  return { messages, status, error, sendMessage, stop }
}
