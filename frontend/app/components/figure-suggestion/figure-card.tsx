import { FileTextIcon } from 'lucide-react'

import { Button } from '~/components/ui/button'
import type { FigureSuggestionItem } from '~/hooks/use-figure-suggestion'

type FigureCardProps = {
  item: FigureSuggestionItem
  onSelect: (item: FigureSuggestionItem) => void
}

export function FigureCard({ item, onSelect }: FigureCardProps) {
  return (
    <Button
      variant="ghost"
      onClick={() => onSelect(item)}
      className="group relative mb-4 block h-auto w-full break-inside-avoid overflow-hidden whitespace-normal rounded-xl border border-border bg-card p-0 text-left shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:bg-card hover:shadow-xl"
    >
      <img
        src={item.image_url}
        alt={item.caption ?? '論文中の図'}
        loading="lazy"
        className="w-full bg-white object-contain"
      />

      <div className="pointer-events-none absolute inset-x-0 bottom-0 translate-y-2 bg-gradient-to-t from-black/80 via-black/40 to-transparent p-3 opacity-0 transition-all duration-200 group-hover:translate-y-0 group-hover:opacity-100">
        {item.caption && (
          <p className="line-clamp-2 text-xs leading-snug text-white">
            {item.caption}
          </p>
        )}
        <div className="mt-1.5 flex items-center gap-1.5 text-[11px] text-white/80">
          <FileTextIcon className="size-3 shrink-0" />
          <span className="truncate">{item.paper_title ?? item.paper_id}</span>
          <span className="shrink-0">· p.{item.page_number}</span>
        </div>
      </div>
    </Button>
  )
}
