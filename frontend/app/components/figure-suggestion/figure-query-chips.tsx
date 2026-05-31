import { SearchIcon } from 'lucide-react'

import { Badge } from '~/components/ui/badge'

type FigureQueryChipsProps = {
  queries: string[]
}

/** Shows the AI-generated search queries that produced the results. */
export function FigureQueryChips({ queries }: FigureQueryChipsProps) {
  if (queries.length === 0) return null

  return (
    <div className="flex flex-col gap-2">
      <p className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
        <SearchIcon className="size-3.5" />
        AI が生成した検索クエリ
      </p>
      <div className="flex flex-wrap items-center gap-2">
        {queries.map(query => (
          <Badge key={query} variant="outline" className="px-3 py-1">
            {query}
          </Badge>
        ))}
      </div>
    </div>
  )
}
