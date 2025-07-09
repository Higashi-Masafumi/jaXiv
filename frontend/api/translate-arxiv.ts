import {
  type TranslateArxivEvent,
  TranslateArxivEventStatus,
} from "./translate-events";

/**
 * arXiv論文を翻訳し、SSEで進捗を受信する
 * @param arxivPaperId arXiv論文のID
 * @param targetLanguage 翻訳先言語
 * @param onEvent イベントを受信したときのコールバック
 */
export const translateArxivWithEventSource = (
  arxivPaperId: string,
  targetLanguage: "japanese",
  onEvent: (event: TranslateArxivEvent) => void
): EventSource => {
  const es = new EventSource(
    `http://localhost:8000/api/v1/translate/arxiv/${arxivPaperId}?target_language=${targetLanguage}`
  );

  es.onmessage = (event) => {
    console.log("event.data", event.data);
    const data = JSON.parse(event.data);
    onEvent(data);
  };

  es.onerror = (event: Event) => {
    console.error("EventSource error:", event);
    onEvent({
      arxiv_paper_id: arxivPaperId,
      status: TranslateArxivEventStatus.FAILED,
      message:
        "EventSource connection error. The server might be down or unreachable.",
    });
    es.close(); // エラー発生時に接続を閉じる
  };

  return es;
};
