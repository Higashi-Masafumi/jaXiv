import { createWorkersAI } from 'workers-ai-provider'
import {
  convertToModelMessages,
  generateText,
  streamText,
  tool,
  type UIMessage,
} from 'ai'
import { z } from 'zod'

import {
  ragSearchImageApiV1BlogPaperIdRagImagePost,
  ragSearchTextApiV1BlogPaperIdRagTextPost,
} from '~/api/sdk.gen'

const MAX_TOOL_CALLS = 3

export async function createRagChatResponse(options: {
  messages: UIMessage[]
  paperId: string
  apiBaseUrl: string
  aiBinding: Ai
  title?: string
  summary?: string
}): Promise<Response> {
  const { messages, paperId, apiBaseUrl, aiBinding, title, summary } = options
  const workersai = createWorkersAI({ binding: aiBinding })

  const modelMessages = await convertToModelMessages(messages)

  const paperSection =
    title && summary
      ? `\n\n対象論文の情報：\nタイトル: ${title}\n概要: ${summary}`
      : ''

  const systemPrompt = `あなたは論文の内容についての質問に答えるアシスタントです。
    論文の内容を検索するツールを使用して、必要な情報を取得してユーザーの質問に対して事実に基づいた正確な回答を行なってください。
    回答はマークダウン形式で行い、数式はKaTeX対応の形式で記述してください。${paperSection}
    `

  const tools = {
    textSearch: tool({
      description:
        '論文本文チャンクの意味的検索。要約・定義・手法の説明などテキストに関する質問に使う。',
      inputSchema: z.object({
        query: z.string().describe('検索クエリ（自然言語）'),
      }),
      execute: async ({ query }) => {
        const { data, error } = await ragSearchTextApiV1BlogPaperIdRagTextPost({
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
  }

  // Phase 1: ツールを使って情報収集（上限 MAX_TOOL_CALLS 回）
  const gathered = await generateText({
    model: workersai('@cf/nvidia/nemotron-3-120b-a12b'),
    system: systemPrompt,
    messages: modelMessages,
    tools,
    stopWhen: ({ steps }) => {
      const toolCallCount = steps.reduce(
        (count, step) => count + (step.toolCalls?.length ?? 0),
        0,
      )
      return toolCallCount >= MAX_TOOL_CALLS
    },
  })

  // Phase 2: 収集したツール結果を含むメッセージ履歴から最終回答をストリーミング
  const result = streamText({
    model: workersai('@cf/nvidia/nemotron-3-120b-a12b'),
    system: systemPrompt,
    messages: [...modelMessages, ...gathered.response.messages],
  })

  return result.toUIMessageStreamResponse()
}
