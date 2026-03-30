import { Link } from 'react-router'

import { listBlogsApiV1BlogGet } from '../api/sdk.gen'
import { Skeleton } from '../components/ui/skeleton'
import type { Route } from './+types/blog'

export function meta() {
  return [
    { title: 'アーカイブ | jaXiv' },
    { name: 'description', content: '生成済みのブログ記事一覧' },
  ]
}

export async function clientLoader() {
  const { data, error } = await listBlogsApiV1BlogGet({
    baseUrl: import.meta.env.VITE_API_BASE_URL,
  })
  if (error || !data)
    throw new Response('Failed to load archive', { status: 500 })
  return data
}

export function HydrateFallback() {
  return (
    <main className="px-4 py-12">
      <div className="mx-auto max-w-3xl">
        <h1 className="mb-8 text-2xl font-bold text-foreground">アーカイブ</h1>
        <Skeleton className="h-10 w-full" />
      </div>
      <div className="mx-auto max-w-3xl">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
      </div>
    </main>
  )
}

export default function BlogList({ loaderData }: Route.ComponentProps) {
  if (loaderData.length === 0) {
    return (
      <main className="px-4 py-12">
        <div className="mx-auto max-w-3xl">
          <h1 className="mb-8 text-2xl font-bold text-foreground">
            アーカイブ
          </h1>
          <p className="text-muted-foreground">まだブログ記事がありません。</p>
        </div>
      </main>
    )
  }

  return (
    <main className="px-4 py-12">
      <div className="mx-auto max-w-3xl">
        <h1 className="mb-8 text-2xl font-bold text-foreground">アーカイブ</h1>
        <ul className="flex flex-col gap-4">
          {loaderData.map(post => (
            <li key={post.paper_id}>
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
                  <span>
                    {new Date(post.created_at).toLocaleDateString('ja-JP')}
                  </span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </main>
  )
}
