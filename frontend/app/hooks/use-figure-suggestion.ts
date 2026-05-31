import { useCallback, useState } from 'react'

import { suggestFiguresApiV1FiguresSuggestPost } from '~/api/sdk.gen'
import type { FigureSuggestionItemSchema } from '~/api/types.gen'

export type FigureSuggestStatus = 'idle' | 'loading' | 'success' | 'error'

export type FigureSuggestionItem = FigureSuggestionItemSchema

export function useFigureSuggestion() {
  const [status, setStatus] = useState<FigureSuggestStatus>('idle')
  const [items, setItems] = useState<FigureSuggestionItem[]>([])
  const [error, setError] = useState<string | null>(null)

  const suggest = useCallback(async (query: string) => {
    const trimmed = query.trim()
    if (!trimmed) return
    setStatus('loading')
    setError(null)

    const { data, error: requestError } =
      await suggestFiguresApiV1FiguresSuggestPost({
        body: { query: trimmed, limit: 24 },
      })

    if (!data) {
      setError(
        requestError
          ? '図の検索に失敗しました。しばらくしてからもう一度お試しください。'
          : '図の検索に失敗しました。',
      )
      setStatus('error')
      return
    }

    setItems(data.items)
    setStatus('success')
  }, [])

  return { status, items, error, suggest }
}
