import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router'
import { supabase } from '~/lib/supabase'
import type { ChatRequest } from '~/api/types.gen'

// ---------------------------------------------------------------------------
// Message types for UI rendering
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
// SSE event types (mirrors application/chat_events.py)
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

export type ChatStatus = 'idle' | 'submitted' | 'streaming'

const threadKey = (paperId: string) => `chat_thread_${paperId}`

export function usePaperChat(paperId: string) {
  const [messages, setMessages] = useState<PaperChatMessage[]>([])
  const [status, setStatus] = useState<ChatStatus>('idle')
  const [error, setError] = useState<Error | null>(null)
  const threadIdRef = useRef<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    threadIdRef.current = localStorage.getItem(threadKey(paperId))
  }, [paperId])

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

      const userMsgId = crypto.randomUUID()
      const assistantId = crypto.randomUUID()
      setMessages(prev => [
        ...prev,
        { id: userMsgId, role: 'user', parts: [{ type: 'text', text }] },
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
          case 'thread_id':
            threadIdRef.current = event.thread_id
            localStorage.setItem(threadKey(paperId), event.thread_id)
            break
          case 'block_start':
            updateAssistant(m => ({
              ...m,
              parts: [
                ...m.parts,
                event.block.type === 'text'
                  ? ({ type: 'text', text: '' } satisfies TextPart)
                  : ({
                      type: 'tool-call',
                      toolCallId: event.block.id,
                      name: event.block.name,
                      state: 'executing',
                    } satisfies ToolCallPart),
              ],
            }))
            break
          case 'block_delta':
            if (event.delta.type === 'text_delta') {
              updateAssistant(m => {
                const parts = [...m.parts]
                const idx = parts.findLastIndex(p => p.type === 'text')
                if (idx >= 0)
                  parts[idx] = {
                    type: 'text',
                    text: (parts[idx] as TextPart).text + event.delta.text,
                  }
                return { ...m, parts }
              })
            }
            break
          case 'tool_result':
            updateAssistant(m => ({
              ...m,
              parts: m.parts.map(p =>
                p.type === 'tool-call' && p.toolCallId === event.tool_use_id
                  ? ({ ...p, state: 'done' } satisfies ToolCallPart)
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
        const body: ChatRequest = {
          message: text,
          thread_id: threadIdRef.current,
        }
        const response = await fetch(
          `${import.meta.env.VITE_API_BASE_URL}/api/v1/chat/paper/${encodeURIComponent(paperId)}`,
          {
            method: 'POST',
            signal: abort.signal,
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${session.access_token}`,
            },
            body: JSON.stringify(body),
          },
        )

        if (!response.ok) {
          const msg = await response.text().catch(() => response.statusText)
          throw new Error(`${response.status}: ${msg}`)
        }

        setStatus('streaming')

        const reader = response
          .body!.pipeThrough(new TextDecoderStream())
          .getReader()
        let buf = ''
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buf += value
          buf = buf.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
          const chunks = buf.split('\n\n')
          buf = chunks.pop() ?? ''
          for (const chunk of chunks) {
            const data = chunk
              .split('\n')
              .filter(l => l.startsWith('data:'))
              .map(l => l.slice('data:'.length).trimStart())
              .join('\n')
            if (!data) continue
            try {
              applyEvent(JSON.parse(data) as ChatStreamEvent)
            } catch {
              // malformed event — skip
            }
          }
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
