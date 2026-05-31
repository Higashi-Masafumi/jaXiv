import { Link } from 'react-router'
import { ExternalLinkIcon } from 'lucide-react'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '~/components/ui/dialog'
import type { FigureSuggestionItem } from '~/hooks/use-figure-suggestion'

type FigureLightboxProps = {
  item: FigureSuggestionItem | null
  onClose: () => void
}

export function FigureLightbox({ item, onClose }: FigureLightboxProps) {
  return (
    <Dialog open={item !== null} onOpenChange={open => !open && onClose()}>
      <DialogContent className="max-h-[90vh] gap-4 overflow-y-auto sm:max-w-3xl">
        {item && (
          <>
            <DialogHeader>
              <DialogTitle className="text-base">
                {item.paper_title ?? item.paper_id}
              </DialogTitle>
              <DialogDescription>
                p.{item.page_number} · 検索クエリ: {item.matched_query}
              </DialogDescription>
            </DialogHeader>

            <div className="overflow-hidden rounded-lg border border-border bg-white">
              <img
                src={item.image_url}
                alt={item.caption ?? '論文中の図'}
                className="max-h-[60vh] w-full object-contain"
              />
            </div>

            {item.caption && (
              <p className="text-sm leading-relaxed text-muted-foreground">
                {item.caption}
              </p>
            )}

            <Link
              to={`/blog/${item.paper_id}`}
              className="inline-flex w-fit items-center gap-1.5 text-sm font-medium text-primary underline-offset-4 hover:underline"
            >
              <ExternalLinkIcon className="size-3.5" />
              この図の出典論文を読む
            </Link>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
