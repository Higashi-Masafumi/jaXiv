import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router'
import { chatWithPaperApiV1ChatPaperPaperIdPost } from '~/api/sdk.gen'
import { supabase } from '~/lib/supabase'

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
