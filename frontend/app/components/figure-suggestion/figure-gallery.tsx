import { ImageOffIcon } from 'lucide-react'

import { Skeleton } from '~/components/ui/skeleton'
import { cn } from '~/lib/utils'
import type { FigureSuggestionItem } from '~/hooks/use-figure-suggestion'

import { FigureCard } from './figure-card'

const MASONRY_CLASS = 'columns-1 gap-4 sm:columns-2 lg:columns-3 xl:columns-4'

const SKELETON_COUNT = 8
// Cycled aspect ratios so the loading state reads as a masonry layout.
const SKELETON_ASPECTS = ['aspect-square', 'aspect-[3/4]', 'aspect-[4/3]']

type FigureGalleryProps = {
  items: FigureSuggestionItem[]
  isLoading: boolean
  onSelect: (item: FigureSuggestionItem) => void
}

export function FigureGallery({
  items,
  isLoading,
  onSelect,
}: FigureGalleryProps) {
  if (isLoading) {
    return (
      <div className={MASONRY_CLASS}>
        {Array.from({ length: SKELETON_COUNT }, (_, i) => (
          <Skeleton
            key={i}
            className={cn(
              'mb-4 w-full rounded-xl',
              SKELETON_ASPECTS[i % SKELETON_ASPECTS.length],
            )}
          />
        ))}
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border bg-card/40 px-6 py-16 text-center">
        <ImageOffIcon className="size-8 text-muted-foreground" />
        <p className="text-sm font-medium text-foreground">
          一致する図が見つかりませんでした
        </p>
        <p className="max-w-sm text-sm text-muted-foreground">
          作りたい図の種類や研究分野を変えて、別の言い回しで試してみてください。
        </p>
      </div>
    )
  }

  return (
    <div className={MASONRY_CLASS}>
      {items.map(item => (
        <FigureCard key={item.image_url} item={item} onSelect={onSelect} />
      ))}
    </div>
  )
}
