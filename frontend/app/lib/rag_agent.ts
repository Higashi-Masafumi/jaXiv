import { createWorkersAI } from 'workers-ai-provider'
import {
  convertToModelMessages,
  stepCountIs,
  streamText,
  tool,
  type UIMessage,
} from 'ai'
import { z } from 'zod'

import {
  ragSearchImageApiV1BlogPaperIdRagImagePost,
  ragSearchTextApiV1BlogPaperIdRagTextPost,
} from '~/api/sdk.gen'

export async function createRagChatResponse(options: {
  messages: UIMessage[]
  paperId: string
  apiBaseUrl: string
  aiBinding: Ai
}): Promise<Response> {
  const { messages, paperId, apiBaseUrl, aiBinding } = options
  const workersai = createWorkersAI({ binding: aiBinding })

  const modelMessages = await convertToModelMessages(
    messages as Omit<UIMessage, 'id'>[],
  )

  const result = streamText({
    model: workersai('@cf/meta/llama-3.1-8b-instruct'),
    system: `あなたは論文ブログ記事の横で動くアシスタントです。
与えられた論文（このページの paper_id に対応するインデックス）について、ユーザーの質問に答えてください。
事実は必ず textSearch / imageSearch ツールで取得した内容に基づいて述べてください。
ツール結果にないことは推測せず、不明と言ってください。`,
    messages: modelMessages,
    stopWhen: stepCountIs(5),
    tools: {
      textSearch: tool({
        description:
          '論文本文チャンクの意味的検索。要約・定義・手法の説明などテキストに関する質問に使う。',
        inputSchema: z.object({
          query: z.string().describe('検索クエリ（自然言語）'),
        }),
        execute: async ({ query }) => {
          const { data, error } =
            await ragSearchTextApiV1BlogPaperIdRagTextPost({
              baseUrl: apiBaseUrl,
              path: { paper_id: paperId },
              body: { query, limit: 5 },
            })
          if (error)
            throw new Error(`textSearch failed: ${JSON.stringify(error)}`)
          return data
        },
      }),
      imageSearch: tool({
        description:
          '図・画像に関連する検索。キャプション意味で近い図の画像URLを返す。図やスクリーンショットの話題に使う。',
        inputSchema: z.object({
          query: z.string().describe('検索クエリ（自然言語）'),
        }),
        execute: async ({ query }) => {
          const { data, error } =
            await ragSearchImageApiV1BlogPaperIdRagImagePost({
              baseUrl: apiBaseUrl,
              path: { paper_id: paperId },
              body: { query, limit: 5 },
            })
          if (error)
            throw new Error(`imageSearch failed: ${JSON.stringify(error)}`)
          return data
        },
      }),
    },
  })

  return result.toUIMessageStreamResponse()
}
