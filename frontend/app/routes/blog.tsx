import { Link } from 'react-router'

import { listBlogsApiV1BlogGet } from '../api/sdk.gen'
import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '../components/ui/card'
import { Skeleton } from '../components/ui/skeleton'
import type { Route } from './+types/blog'

function BlogArchiveCardSkeleton() {
  return (
    <Card aria-hidden className="shadow-none">
      <CardHeader className="flex flex-col gap-2">
        <CardTitle className="flex flex-col gap-2 font-normal">
          <Skeleton className="h-5 w-11/12" />
          <Skeleton className="h-5 w-full" />
        </CardTitle>
        <CardDescription className="flex flex-col gap-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-2/3" />
        </CardDescription>
      </CardHeader>
      <CardFooter className="flex w-full gap-3">
        <Skeleton className="h-3.5 flex-1" />
        <Skeleton className="h-3.5 flex-1" />
      </CardFooter>
    </Card>
  )
}

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
    <main className="px-4 py-12" aria-busy="true">
      <div className="mx-auto max-w-3xl">
        <h1 className="mb-8 text-2xl font-bold text-foreground">アーカイブ</h1>
        <ul className="flex flex-col gap-4">
          {Array.from({ length: 4 }, (_, i) => (
            <li key={i}>
              <BlogArchiveCardSkeleton />
            </li>
          ))}
        </ul>
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
