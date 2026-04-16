import { Link } from 'react-router'

import type { BlogPostResponseSchema } from '~/api/types.gen'

export function BlogPostCard({ post }: { post: BlogPostResponseSchema }) {
  return (
    <Link
      to={`/blog/${post.paper_id}`}
      className="block rounded-xl border border-border bg-card p-5 transition-colors hover:bg-accent"
    >
      <h2 className="mb-1 font-semibold text-card-foreground line-clamp-2">
        {post.title}
      </h2>
      {post.summary && (
        <p className="mb-3 text-sm text-muted-foreground line-clamp-2">
          {post.summary}
        </p>
      )}
      <div className="flex items-center gap-3 text-xs text-muted-foreground">
        {post.authors.length > 0 && (
          <span>
            {post.authors.slice(0, 2).join(', ')}
            {post.authors.length > 2 ? ' ほか' : ''}
          </span>
        )}
        <span>{new Date(post.created_at).toLocaleDateString('ja-JP')}</span>
      </div>
    </Link>
  )
}
