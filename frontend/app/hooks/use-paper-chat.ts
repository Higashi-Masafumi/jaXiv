/**
 * usePaperChat — replaces Vercel AI SDK's useChat.
 *
 * Streams chat responses from the FastAPI backend using the Anthropic-inspired
 * block protocol (BlockStart / BlockDelta / BlockStop + ToolResult events).
 * Thread IDs are persisted in localStorage so conversations survive page reloads.
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import { supabase } from '~/lib/supabase'

// ---------------------------------------------------------------------------
// Local message types
// (will be replaced by hey-api generated types after `npm run generate-api`)
// ---------------------------------------------------------------------------

export type TextPart = { type: 'text'; text: string }
export type ToolCallPart = {
  type: 'tool-call'
  toolCallId: string
  name: string
  state: 'executing' | 'done' | 'error'
}
export type MessagePart = TextPart | ToolCallPart

export type PaperChatMessage = {
  id: string
  role: 'user' | 'assistant'
  parts: MessagePart[]
}

// ---------------------------------------------------------------------------
// SSE event types (mirrors application/chat_events.py on the backend)
// ---------------------------------------------------------------------------

type ThreadIdEvent = { type: 'thread_id'; thread_id: string }
type BlockStartEvent =
  | { type: 'block_start'; index: number; block: { type: 'text' } }
  | {
      type: 'block_start'
      index: number
      block: { type: 'tool_use'; id: string; name: string }
    }
type BlockDeltaEvent = {
  type: 'block_delta'
  index: number
  delta: { type: 'text_delta'; text: string }
}
type BlockStopEvent = { type: 'block_stop'; index: number }
type ToolResultEvent = {
  type: 'tool_result'
  tool_use_id: string
  name: string
  content: unknown
}
type MessageStopEvent = { type: 'message_stop' }
type ErrorEvent = { type: 'error'; message: string }

type ChatStreamEvent =
  | ThreadIdEvent
  | BlockStartEvent
  | BlockDeltaEvent
  | BlockStopEvent
  | ToolResultEvent
  | MessageStopEvent
  | ErrorEvent

// ---------------------------------------------------------------------------

const threadKey = (paperId: string) => `chat_thread_${paperId}`

export type ChatStatus = 'idle' | 'submitted' | 'streaming'

export function usePaperChat(paperId: string) {
  const [messages, setMessages] = useState<PaperChatMessage[]>([])
  const [status, setStatus] = useState<ChatStatus>('idle')
  const [error, setError] = useState<Error | null>(null)
  const threadIdRef = useRef<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  // Restore thread_id from localStorage on mount / paperId change
  useEffect(() => {
    threadIdRef.current = localStorage.getItem(threadKey(paperId))
  }, [paperId])

  const sendMessage = useCallback(
    async (text: string) => {
      if (status !== 'idle') return

      // Auth check — login required, anonymous blocked
      const {
        data: { session },
      } = await supabase.auth.getSession()
      if (!session || session.user.is_anonymous) {
        setError(
          new Error(
            'チャットを使用するにはGoogleアカウントでログインしてください',
          ),
        )
        return
      }

      // Optimistically add user message
      const userMsgId = crypto.randomUUID()
      setMessages(prev => [
        ...prev,
        { id: userMsgId, role: 'user', parts: [{ type: 'text', text }] },
      ])
      setStatus('submitted')
      setError(null)

      // Placeholder for the streaming assistant message
      const assistantId = crypto.randomUUID()
      setMessages(prev => [
        ...prev,
        { id: assistantId, role: 'assistant', parts: [] },
      ])

      const abort = new AbortController()
      abortRef.current = abort

      const updateAssistant = (
        updater: (m: PaperChatMessage) => PaperChatMessage,
      ) => {
        setMessages(prev =>
          prev.map(m => (m.id === assistantId ? updater(m) : m)),
        )
      }

      const applyEvent = (event: ChatStreamEvent) => {
        switch (event.type) {
          case 'thread_id': {
            threadIdRef.current = event.thread_id
            localStorage.setItem(threadKey(paperId), event.thread_id)
            break
          }
          case 'block_start': {
            if (event.block.type === 'text') {
              updateAssistant(m => ({
                ...m,
                parts: [
                  ...m.parts,
                  { type: 'text', text: '' } satisfies TextPart,
                ],
              }))
            } else {
              updateAssistant(m => ({
                ...m,
                parts: [
                  ...m.parts,
                  {
                    type: 'tool-call',
                    toolCallId: event.block.id,
                    name: event.block.name,
                    state: 'executing',
                  } satisfies ToolCallPart,
                ],
              }))
            }
            break
          }
          case 'block_delta': {
            if (event.delta.type === 'text_delta') {
              updateAssistant(m => {
                const parts = [...m.parts]
                const idx = parts.findLastIndex(p => p.type === 'text')
                if (idx >= 0) {
                  parts[idx] = {
                    type: 'text',
                    text: (parts[idx] as TextPart).text + event.delta.text,
                  }
                }
                return { ...m, parts }
              })
            }
            break
          }
          case 'tool_result': {
            updateAssistant(m => ({
              ...m,
              parts: m.parts.map(p =>
                p.type === 'tool-call' && p.toolCallId === event.tool_use_id
                  ? ({ ...p, state: 'done' } satisfies ToolCallPart)
                  : p,
              ),
            }))
            break
          }
          case 'error': {
            setError(new Error(event.message))
            break
          }
          default:
            break
        }
      }

      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_BASE_URL}/api/v1/chat/paper/${encodeURIComponent(paperId)}`,
          {
            method: 'POST',
            signal: abort.signal,
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${session.access_token}`,
            },
            body: JSON.stringify({
              message: text,
              thread_id: threadIdRef.current,
            }),
          },
        )

        if (!response.ok) {
          const body = await response.text().catch(() => response.statusText)
          throw new Error(`${response.status}: ${body}`)
        }

        setStatus('streaming')

        // Read the SSE response body line-by-line
        const reader = response
          .body!.pipeThrough(new TextDecoderStream())
          .getReader()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += value
          buffer = buffer.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
          const chunks = buffer.split('\n\n')
          buffer = chunks.pop() ?? ''

          for (const chunk of chunks) {
            const dataLines = chunk
              .split('\n')
              .filter(l => l.startsWith('data:'))
              .map(l => l.slice('data:'.length).trimStart())

            if (!dataLines.length) continue
            try {
              const event = JSON.parse(dataLines.join('\n')) as ChatStreamEvent
              applyEvent(event)
            } catch {
              // malformed event — skip
            }
          }
        }
      } catch (e) {
        if (e instanceof Error && e.name === 'AbortError') return
        setError(e instanceof Error ? e : new Error(String(e)))
        // Remove empty assistant placeholder on error
        setMessages(prev =>
          prev.filter(m => !(m.id === assistantId && m.parts.length === 0)),
        )
      } finally {
        setStatus('idle')
        abortRef.current = null
      }
    },
    [paperId, status],
  )

  const stop = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  return { messages, status, error, sendMessage, stop }
}
