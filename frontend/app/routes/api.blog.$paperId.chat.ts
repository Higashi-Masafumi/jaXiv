import type { UIMessage } from 'ai'
import type { Route } from './+types/api.blog.$paperId.chat'
import { getBlogApiV1BlogPaperIdGet } from '~/api/sdk.gen'
import { createRagChatResponse } from '~/lib/rag_agent'

export async function action({ request, context, params }: Route.ActionArgs) {
  const { messages }: { messages: UIMessage[] } = await request.json()
  const paperId = params.paperId!
  const apiBaseUrl = context.cloudflare.env.API_BASE_URL

  const { data: blog } = await getBlogApiV1BlogPaperIdGet({
    baseUrl: apiBaseUrl,
    path: { paper_id: paperId },
  })

  const paperContext = blog
    ? { title: blog.title, summary: blog.summary, authors: blog.authors }
    : undefined

  return await createRagChatResponse({
    messages,
    paperId,
    apiBaseUrl,
    aiBinding: context.cloudflare.env.AI,
    paperContext,
  })
}
