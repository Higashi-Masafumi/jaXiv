import { useCallback, useState } from 'react'

import { suggestFiguresApiV1FiguresSuggestPost } from '~/api/sdk.gen'
import type { FigureSuggestionItemSchema } from '~/api/types.gen'

export type FigureSuggestStatus = 'idle' | 'loading' | 'success' | 'error'

export type FigureSuggestionItem = FigureSuggestionItemSchema

export function useFigureSuggestion() {
  const [status, setStatus] = useState<FigureSuggestStatus>('idle')
  const [queries, setQueries] = useState<string[]>([])
  const [items, setItems] = useState<FigureSuggestionItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [lastQuery, setLastQuery] = useState<string>('')

  const suggest = useCallback(async (query: string) => {
    const trimmed = query.trim()
    if (!trimmed) return
    setStatus('loading')
    setError(null)
    setLastQuery(trimmed)

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

    setQueries(data.queries)
    setItems(data.items)
    setStatus('success')
  }, [])

  const reset = useCallback(() => {
    setStatus('idle')
    setQueries([])
    setItems([])
    setError(null)
    setLastQuery('')
  }, [])

  return { status, queries, items, error, lastQuery, suggest, reset }
}
