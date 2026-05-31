import { useActionState } from 'react'

import { suggestFiguresApiV1FiguresSuggestPost } from '~/api/sdk.gen'
import type { FigureSuggestionItemSchema } from '~/api/types.gen'

export type FigureSuggestionItem = FigureSuggestionItemSchema

type FigureSuggestState = {
  items: FigureSuggestionItem[]
  error: string | null
  submitted: boolean
}

const INITIAL_STATE: FigureSuggestState = {
  items: [],
  error: null,
  submitted: false,
}

/**
 * Manages the figure-search submission lifecycle via React's `useActionState`.
 * `submit(query)` runs the search; `isPending` tracks the in-flight request.
 */
export function useFigureSuggestion() {
  const [state, submit, isPending] = useActionState(
    async (
      _prev: FigureSuggestState,
      query: string,
    ): Promise<FigureSuggestState> => {
      const { data, error } = await suggestFiguresApiV1FiguresSuggestPost({
        body: { query, limit: 24 },
      })
      if (!data) {
        return {
          items: [],
          error: error
            ? '図の検索に失敗しました。しばらくしてからもう一度お試しください。'
            : '図の検索に失敗しました。',
          submitted: true,
        }
      }
      return { items: data.items, error: null, submitted: true }
    },
    INITIAL_STATE,
  )

  return {
    items: state.items,
    error: state.error,
    submitted: state.submitted,
    isPending,
    submit,
  }
}
