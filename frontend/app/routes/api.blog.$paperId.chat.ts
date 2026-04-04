import type { UIMessage } from 'ai'
import type { ActionFunctionArgs } from 'react-router'
import { createRagChatResponse } from '~/lib/rag_agent'

export async function action({ request, context, params }: ActionFunctionArgs) {
  const { messages }: { messages: UIMessage[] } = await request.json()
  return await createRagChatResponse({
    messages,
    paperId: params.paperId!,
    apiBaseUrl: context.cloudflare.env.API_BASE_URL,
    aiBinding: context.cloudflare.env.AI,
  })
}
