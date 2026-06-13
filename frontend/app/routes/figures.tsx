import { useMemo, useState } from 'react'
import { ImagesIcon } from 'lucide-react'

import { useAuth } from '~/contexts/auth-context'
import {
  useFigureSuggestion,
  type FigureSuggestionItem,
} from '~/hooks/use-figure-suggestion'
import { GenerationHero } from '~/components/generation-hero'
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
  const { isAnonymous } = useAuth()
  const { items, error, submitted, isPending, submit } = useFigureSuggestion()
  const [selected, setSelected] = useState<FigureSuggestionItem | null>(null)

  // The distinct AI-generated queries that surfaced the results, shown as chips.
  const queries = useMemo(
    () => [...new Set(items.map(item => item.matched_query))],
    [items],
  )

  return (
    <main className="h-full overflow-y-auto bg-background">
      <GenerationHero
        icon={ImagesIcon}
        badge="AI が論文を横断して図を提案"
        titleLead="作りたい図を、"
        titleHighlight="論文から見つける。"
        description="作りたい図や研究内容を入力すると、AI が検索クエリを組み立て、論文全体から参考になる図を探します。"
      >
        <div className="mt-7">
          <FigureSearchComposer
            isLoading={isPending}
            disabled={isAnonymous}
            onSubmit={submit}
          />

          {error && <p className="mt-3 text-sm text-destructive">{error}</p>}
        </div>
      </GenerationHero>

      {(isPending || (submitted && !error)) && (
        <div className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6">
          {isPending ? (
            <FigureGallery items={[]} isLoading onSelect={setSelected} />
          ) : (
            <div className="flex flex-col gap-5">
              <FigureQueryChips queries={queries} />
              <FigureGallery
                items={items}
                isLoading={false}
                onSelect={setSelected}
              />
            </div>
          )}
        </div>
      )}

      <FigureLightbox item={selected} onClose={() => setSelected(null)} />
    </main>
  )
}
