import type { ChatMessageResponse } from '~/api/types.gen'
import type {
  MessagePart,
  PaperChatMessage,
  ToolCallPart,
} from '~/hooks/use-paper-chat'

function parseToolResult(content: string | null | undefined): unknown {
  if (!content) return null
  try {
    return JSON.parse(content)
  } catch {
    return content
  }
}

export function historyToMessages(
  messages: ChatMessageResponse[] | null | undefined,
): PaperChatMessage[] {
  if (!messages || messages.length === 0) return []

  const out: PaperChatMessage[] = []
  let lastAssistant: PaperChatMessage | null = null

  for (const m of messages) {
    if (m.role === 'user') {
      out.push({
        id: m.id,
        role: 'user',
        parts: m.content ? [{ type: 'text', text: m.content }] : [],
      })
      lastAssistant = null
      continue
    }

    if (m.role === 'assistant') {
      const parts: MessagePart[] = []
      if (m.content) parts.push({ type: 'text', text: m.content })
      if (m.tool_calls) {
        for (const call of m.tool_calls) {
          parts.push({
            type: 'tool-call',
            toolCallId: call.id,
            name: call.name,
            input: call.args ?? {},
            result: null,
            state: 'done',
          })
        }
      }
      const message: PaperChatMessage = { id: m.id, role: 'assistant', parts }
      out.push(message)
      lastAssistant = message
      continue
    }

    if (m.role === 'tool' && lastAssistant && m.tool_call_id) {
      lastAssistant.parts = lastAssistant.parts.map(part => {
        if (part.type !== 'tool-call') return part
        if (part.toolCallId !== m.tool_call_id) return part
        const result = parseToolResult(m.content)
        return {
          ...part,
          state: 'done',
          result:
            result && typeof result === 'object' && !Array.isArray(result)
              ? (result as ToolCallPart['result'])
              : { value: result },
        }
      })
    }
  }

  return out
}
