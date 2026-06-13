import { Link } from 'react-router'
import { FileTextIcon } from 'lucide-react'

import type { BlogPostResponseSchema } from '~/api/types.gen'

export function BlogPostCard({ post }: { post: BlogPostResponseSchema }) {
  return (
    <Link
      to={`/blog/${post.paper_id}`}
      className="group flex h-full flex-col rounded-xl border border-border bg-card p-5 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-md"
    >
      {/* Paper ID badge */}
      <div className="mb-3 flex items-center gap-1.5">
        <FileTextIcon className="size-3 shrink-0 text-muted-foreground/70" />
        <span className="font-mono text-[10px] tracking-wide text-muted-foreground/70">
          {post.paper_id}
        </span>
      </div>

      {/* Title */}
      <h2 className="mb-2 flex-1 text-sm font-semibold leading-snug text-card-foreground line-clamp-3 group-hover:text-primary transition-colors duration-200">
        {post.title}
      </h2>

      {/* Summary */}
      {post.summary && (
        <p className="mb-4 text-xs leading-relaxed text-muted-foreground line-clamp-2">
          {post.summary}
        </p>
      )}

      {/* Metadata */}
      <div className="mt-auto flex items-center justify-between gap-2 border-t border-border/60 pt-3 text-xs text-muted-foreground">
        {post.authors.length > 0 && (
          <span className="min-w-0 truncate">
            {post.authors.slice(0, 2).join(', ')}
            {post.authors.length > 2 ? ' ほか' : ''}
          </span>
        )}
        <span className="shrink-0 tabular-nums">
          {new Date(post.created_at).toLocaleDateString('ja-JP')}
        </span>
      </div>
    </Link>
  )
}
