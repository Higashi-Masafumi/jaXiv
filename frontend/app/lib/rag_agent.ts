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

  const modelMessages = await convertToModelMessages(messages)

  const result = streamText({
    model: workersai('@cf/meta/llama-3.3-70b-instruct-fp8-fast'),
    system: `あなたは論文の内容についての質問に答えるアシスタントです。
    論文の内容を検索するツールを使用して、必要な情報を取得してユーザーの質問に対して事実に基づいた正確な回答を行なってください。
    回答はマークダウン形式で行い、数式はKaTeX対応の形式で記述してください。
    `,
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
