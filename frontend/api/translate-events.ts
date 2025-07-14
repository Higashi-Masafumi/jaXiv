export enum TranslateArxivEventStatus {
  PROGRESS = "progress",
  COMPLETED = "completed",
  FAILED = "failed",
}

export interface TranslateArxivProgressEvent {
  status: TranslateArxivEventStatus.PROGRESS;
  arxiv_paper_id: string;
  message: string;
  progress_percentage: number;
}

export interface TranslateArxivCompletedEvent {
  status: TranslateArxivEventStatus.COMPLETED;
  arxiv_paper_id: string;
  message: string;
  translated_pdf_url: string;
  progress_percentage: number;
}

export interface TranslateArxivFailedEvent {
  status: TranslateArxivEventStatus.FAILED;
  arxiv_paper_id: string;
  message: string;
  progress_percentage: number;
}

export type TranslateArxivEvent =
  | TranslateArxivProgressEvent
  | TranslateArxivCompletedEvent
  | TranslateArxivFailedEvent;
