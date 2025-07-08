import createFetchClient from "openapi-fetch";
import createClient from "openapi-react-query";
import type { paths } from "./schema";
import type { TranslateArxivEvent } from "../app/types/translate-events";

const fetchClient = createFetchClient<paths>({
  baseUrl: "http://localhost:8000",
});

const $api = createClient<paths>(fetchClient);

export { $api };

/**
 * arXiv論文を翻訳し、SSEで進捗を受信する
 * @param arxivPaperId arXiv論文のID
 * @param targetLanguage 翻訳先言語
 * @param onEvent イベントを受信したときのコールバック
 * @param signal AbortSignal（キャンセル用）
 */
export async function translateArxivWithSSE(
  arxivPaperId: string,
  targetLanguage: "japanese",
  onEvent: (event: TranslateArxivEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  // openapi-fetchを使用してSSEリクエストを送信
  const response = await fetchClient.POST("/api/v1/translate/arxiv", {
    body: {
      arxiv_paper_id: arxivPaperId,
      target_language: targetLanguage,
    },
    signal,
    // SSE用のヘッダーを設定
    headers: {
      Accept: "text/event-stream",
      "Cache-Control": "no-cache",
    },
  });

  if (response.error) {
    throw new Error(`API Error: ${response.error}`);
  }

  if (!response.response?.body) {
    throw new Error("No response body");
  }

  const reader = response.response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");

      // 最後の不完全な行を保持
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6); // "data: " を除去
          if (data.trim() === "") continue;

          try {
            // sse-starlette はJSONをダブルクォートでエスケープして送信するため、
            // まずJSONパースしてから再度パースする必要がある
            const parsedData = JSON.parse(data);
            const event =
              typeof parsedData === "string"
                ? JSON.parse(parsedData)
                : parsedData;
            onEvent(event as TranslateArxivEvent);
          } catch (error) {
            console.error("Failed to parse SSE event:", error, "Data:", data);
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
