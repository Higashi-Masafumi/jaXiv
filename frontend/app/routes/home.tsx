import { type MetaFunction } from "react-router";
import React, { useState, useRef } from "react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Progress } from "../components/ui/progress";
import { Toaster } from "../components/ui/sonner";
import { toast } from "sonner";
import { extractArxivId } from "../lib/arxiv-utils";
import { translateArxivWithSSE } from "../../api/translate-arxiv";
import type { TranslateArxivEvent } from "../types/translate-events";
import { TranslateArxivEventStatus } from "../types/translate-events";
import {
  CheckCircle2,
  FileText,
  Loader2,
  Copy,
  ExternalLink,
  Download,
  AlertTriangle,
} from "lucide-react";

export const meta: MetaFunction = () => {
  return [
    { title: "arXiv翻訳ツール" },
    { name: "description", content: "arXiv論文を日本語に翻訳するツール" },
  ];
};

interface TranslationState {
  isTranslating: boolean;
  status: TranslateArxivEventStatus | null;
  message: string;
  progressMessages: string[];
  pdfUrl?: string;
  error?: string;
}

export default function Home() {
  const [arxivUrl, setArxivUrl] = useState("");
  const [state, setState] = useState<TranslationState>({
    isTranslating: false,
    status: null,
    message: "",
    progressMessages: [],
  });
  const abortControllerRef = useRef<AbortController | null>(null);

  const handleTranslate = async () => {
    const arxivId = extractArxivId(arxivUrl);

    if (!arxivId) {
      toast.error("無効なarXiv URLです", {
        description:
          "正しいarXiv URLまたはIDを入力してください（例: 2405.12345）",
      });
      return;
    }

    // 状態をリセット
    setState({
      isTranslating: true,
      status: TranslateArxivEventStatus.PROGRESS,
      message: "翻訳を開始しています...",
      progressMessages: [],
    });

    // 前回のリクエストをキャンセル
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    try {
      await translateArxivWithSSE(
        arxivId,
        "japanese",
        (event: TranslateArxivEvent) => {
          setState((prev) => {
            if (event.status === TranslateArxivEventStatus.PROGRESS) {
              return {
                ...prev,
                status: event.status,
                message: event.message,
                progressMessages: [...prev.progressMessages, event.message],
                error: undefined,
              };
            } else if (event.status === TranslateArxivEventStatus.COMPLETED) {
              return {
                ...prev,
                isTranslating: false,
                status: event.status,
                message: event.message,
                progressMessages: [...prev.progressMessages, event.message],
                pdfUrl: event.translated_pdf_url,
                error: undefined,
              };
            } else if (event.status === TranslateArxivEventStatus.FAILED) {
              return {
                ...prev,
                isTranslating: false,
                status: event.status,
                error: event.message,
                message: event.message,
              };
            }

            return prev;
          });

          // 完了または失敗時の通知
          if (event.status === TranslateArxivEventStatus.COMPLETED) {
            toast.success("翻訳が完了しました！", {
              description: "PDFのダウンロードが可能です。",
            });
          } else if (event.status === TranslateArxivEventStatus.FAILED) {
            toast.error("翻訳に失敗しました", {
              description: event.message,
            });
          }
        },
        abortControllerRef.current.signal
      );
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        toast.info("翻訳がキャンセルされました");
      } else {
        const errorMessage =
          error instanceof Error ? error.message : "不明なエラー";
        toast.error("エラーが発生しました", {
          description: errorMessage,
        });
        setState((prev) => ({
          ...prev,
          isTranslating: false,
          error: "接続エラーが発生しました。",
        }));
      }
    }
  };

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setState({
        isTranslating: false,
        status: null,
        message: "",
        progressMessages: [],
      });
    }
  };

  const handleCopyUrl = () => {
    if (state.pdfUrl) {
      navigator.clipboard.writeText(state.pdfUrl);
      toast.success("URLをコピーしました");
    }
  };

  return (
    <>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
        <div className="max-w-4xl mx-auto p-6 space-y-8">
          {/* ヘッダー */}
          <div className="text-center space-y-4 py-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full mb-4">
              <FileText className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              arXiv論文翻訳ツール
            </h1>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              最新のAI技術でarXiv論文を高品質な日本語に翻訳
            </p>
          </div>

          {/* 入力フォーム */}
          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader className="text-center">
              <CardTitle className="text-2xl">論文URLを入力</CardTitle>
              <CardDescription className="text-base">
                arXivの論文URL、またはarXiv IDを入力してください
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex space-x-3">
                <Input
                  placeholder="例: https://arxiv.org/abs/2405.12345 または 2405.12345"
                  value={arxivUrl}
                  onChange={(e) => setArxivUrl(e.target.value)}
                  disabled={state.isTranslating}
                  className="flex-1 h-12 text-base"
                />
                {!state.isTranslating ? (
                  <Button
                    onClick={handleTranslate}
                    disabled={!arxivUrl.trim()}
                    size="lg"
                    className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
                  >
                    <FileText className="mr-2 h-5 w-5" />
                    翻訳開始
                  </Button>
                ) : (
                  <Button
                    onClick={handleCancel}
                    variant="destructive"
                    size="lg"
                  >
                    キャンセル
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* 進捗表示 */}
          {(state.isTranslating || state.status || state.error) && (
            <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="flex items-center justify-between text-xl">
                  <span>翻訳状況</span>
                  {state.status === TranslateArxivEventStatus.PROGRESS && (
                    <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
                  )}
                  {state.status === TranslateArxivEventStatus.COMPLETED && (
                    <CheckCircle2 className="h-6 w-6 text-green-600" />
                  )}
                  {state.error && (
                    <AlertTriangle className="h-6 w-6 text-red-500" />
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {state.error ? (
                  <div className="text-center p-8 text-red-600">
                    <AlertTriangle className="h-12 w-12 mx-auto mb-4" />
                    <p className="text-lg font-medium">{state.error}</p>
                  </div>
                ) : (
                  <>
                    {/* 現在の状態 */}
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <p className="text-lg font-medium text-blue-800">
                        {state.message}
                      </p>
                      {state.status === TranslateArxivEventStatus.PROGRESS && (
                        <Progress className="mt-3 h-2" value={33} />
                      )}
                    </div>

                    {/* 進捗メッセージ一覧 */}
                    {state.progressMessages.length > 0 && (
                      <div className="space-y-3">
                        <h4 className="text-lg font-medium">処理履歴</h4>
                        <div className="max-h-60 overflow-y-auto space-y-2 bg-gray-50 rounded-lg p-4">
                          {state.progressMessages.map((msg, index) => (
                            <div
                              key={index}
                              className="flex items-start text-sm"
                            >
                              <span className="mr-3 text-blue-500 font-bold">
                                {index + 1}.
                              </span>
                              <span className="text-gray-700">{msg}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 完了時のアクション */}
                    {state.status === TranslateArxivEventStatus.COMPLETED &&
                      state.pdfUrl && (
                        <div className="border-t pt-6 space-y-4">
                          <div className="flex items-center space-x-2 bg-green-50 p-4 rounded-lg">
                            <FileText className="h-5 w-5 text-green-600" />
                            <span className="text-sm flex-1 truncate text-green-800">
                              {state.pdfUrl}
                            </span>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={handleCopyUrl}
                              className="text-green-600 hover:text-green-700"
                            >
                              <Copy className="h-4 w-4" />
                            </Button>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            <Button
                              asChild
                              className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
                            >
                              <a
                                href={state.pdfUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                <ExternalLink className="mr-2 h-4 w-4" />
                                PDFを開く
                              </a>
                            </Button>
                            <Button
                              asChild
                              variant="outline"
                              className="border-green-200 text-green-700 hover:bg-green-50"
                            >
                              <a href={state.pdfUrl} download>
                                <Download className="mr-2 h-4 w-4" />
                                ダウンロード
                              </a>
                            </Button>
                          </div>
                        </div>
                      )}
                  </>
                )}
              </CardContent>
            </Card>
          )}

          {/* PDF プレビュー */}
          {state.status === TranslateArxivEventStatus.COMPLETED &&
            state.pdfUrl && (
              <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-xl">PDFプレビュー</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="w-full h-[600px] border-2 border-gray-200 rounded-lg overflow-hidden bg-gray-50">
                    <iframe
                      src={state.pdfUrl}
                      className="w-full h-full"
                      title="翻訳済みPDF"
                    />
                  </div>
                </CardContent>
              </Card>
            )}
        </div>
      </div>
      <Toaster />
    </>
  );
}
