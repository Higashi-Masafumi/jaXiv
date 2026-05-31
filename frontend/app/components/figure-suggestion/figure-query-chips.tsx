import { SearchIcon, XIcon } from 'lucide-react'

import { Badge } from '~/components/ui/badge'
import { cn } from '~/lib/utils'

type FigureQueryChipsProps = {
  queries: string[]
  activeQuery: string | null
  onToggle: (query: string | null) => void
}

/**
 * Surfaces the AI-generated search queries as filter chips. Clicking a chip
 * filters the gallery to figures matched by that query; clicking the active
 * chip (or "すべて") clears the filter.
 */
export function FigureQueryChips({
  queries,
  activeQuery,
  onToggle,
}: FigureQueryChipsProps) {
  if (queries.length === 0) return null

  return (
    <div className="flex flex-col gap-2">
      <p className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
        <SearchIcon className="size-3.5" />
        AI が生成した検索クエリ
      </p>
      <div className="flex flex-wrap items-center gap-2">
        <Badge
          variant={activeQuery === null ? 'default' : 'outline'}
          asChild
          className="cursor-pointer px-3 py-1"
        >
          <button type="button" onClick={() => onToggle(null)}>
            すべて
          </button>
        </Badge>
        {queries.map(query => {
          const isActive = activeQuery === query
          return (
            <Badge
              key={query}
              variant={isActive ? 'default' : 'outline'}
              asChild
              className={cn(
                'cursor-pointer px-3 py-1 transition-colors',
                !isActive && 'hover:border-hero-accent/50',
              )}
            >
              <button
                type="button"
                onClick={() => onToggle(isActive ? null : query)}
              >
                {query}
                {isActive && <XIcon className="size-3" />}
              </button>
            </Badge>
          )
        })}
      </div>
    </div>
  )
}
