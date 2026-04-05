import type { UIMessage } from 'ai'
import type { Route } from './+types/api.blog.$paperId.chat'
import { createRagChatResponse } from '~/lib/rag_agent'

type PaperContext = {
  title: string
  summary: string
  authors: string[]
}

export async function action({ request, context, params }: Route.ActionArgs) {
  const { messages, paperContext }: { messages: UIMessage[]; paperContext?: PaperContext } =
    await request.json()
  return await createRagChatResponse({
    messages,
    paperId: params.paperId!,
    apiBaseUrl: context.cloudflare.env.API_BASE_URL,
    aiBinding: context.cloudflare.env.AI,
    paperContext,
  })
}
