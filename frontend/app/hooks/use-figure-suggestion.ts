import { startTransition, useActionState, useCallback } from 'react'

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
  const [state, dispatch, isPending] = useActionState<
    FigureSuggestState,
    string
  >(async (_prev, query) => {
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
  }, INITIAL_STATE)

  // The composer dispatches from react-hook-form's async `handleSubmit`
  // callback, which resolves outside the original event's transition. Calling
  // the action there directly would run it outside a transition, so `isPending`
  // never flips and React leaves the transition dangling (which also blocks
  // later `setValue` re-renders). Wrapping the dispatch in `startTransition`
  // gives it a transition scope no matter where `submit` is called from.
  const submit = useCallback(
    (query: string) => {
      startTransition(() => dispatch(query))
    },
    [dispatch],
  )

  return {
    items: state.items,
    error: state.error,
    submitted: state.submitted,
    isPending,
    submit,
  }
}
