import { useMemo, useState } from 'react'
import { LogInIcon } from 'lucide-react'

import { useAuth } from '~/contexts/auth-context'
import {
  useFigureSuggestion,
  type FigureSuggestionItem,
} from '~/hooks/use-figure-suggestion'
import { FigureSearchComposer } from '~/components/figure-suggestion/figure-search-composer'
import { FigureQueryChips } from '~/components/figure-suggestion/figure-query-chips'
import { FigureGallery } from '~/components/figure-suggestion/figure-gallery'
import { FigureLightbox } from '~/components/figure-suggestion/figure-lightbox'

export function meta() {
  return [
    { title: 'jaXiv — 図面提案' },
    {
      name: 'description',
      content:
        '作りたい図や研究内容から、論文全体を横断して参考になる図を提案します。',
    },
  ]
}

export default function Figures() {
  const { isAnonymous, signInWithGoogle } = useAuth()
  const { items, error, submitted, isPending, submit } = useFigureSuggestion()
  const [selected, setSelected] = useState<FigureSuggestionItem | null>(null)

  // The distinct AI-generated queries that surfaced the results, shown as chips.
  const queries = useMemo(
    () => [...new Set(items.map(item => item.matched_query))],
    [items],
  )

  return (
    <main className="relative min-h-[calc(100vh-3rem)] overflow-y-auto bg-hero-background px-4 py-16 text-hero-foreground">
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute -left-20 top-10 h-72 w-72 rounded-full bg-hero-accent-soft/20 blur-3xl" />
        <div className="absolute -right-24 bottom-12 h-80 w-80 rounded-full bg-hero-accent-secondary-soft/20 blur-3xl" />
        <div className="absolute inset-0 bg-gradient-to-b from-hero-accent/10 via-transparent to-transparent" />
      </div>

      <section className="mx-auto flex w-full max-w-2xl flex-col items-center gap-6">
        <FigureSearchComposer isLoading={isPending} onSubmit={submit} />

        {isAnonymous && (
          <div className="w-full rounded-xl border border-hero-accent/40 bg-hero-accent/10 px-4 py-3 text-sm">
            図面提案を利用するにはログインが必要です。
            <button
              type="button"
              onClick={signInWithGoogle}
              className="ml-1 inline-flex items-center gap-1 font-semibold underline underline-offset-2"
            >
              <LogInIcon className="size-3.5" />
              Googleでログイン
            </button>
          </div>
        )}

        {error && <p className="text-sm text-destructive">{error}</p>}
      </section>

      {isPending && (
        <section className="mx-auto mt-10 w-full max-w-7xl">
          <FigureGallery items={[]} isLoading onSelect={setSelected} />
        </section>
      )}

      {!isPending && submitted && !error && (
        <section className="mx-auto mt-10 flex w-full max-w-7xl flex-col gap-5">
          <FigureQueryChips queries={queries} />
          <FigureGallery
            items={items}
            isLoading={false}
            onSelect={setSelected}
          />
        </section>
      )}

      <FigureLightbox item={selected} onClose={() => setSelected(null)} />
    </main>
  )
}
