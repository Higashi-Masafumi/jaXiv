import { Suspense } from 'react'
import { Await, Link, useSearchParams } from 'react-router'

import { listBlogsApiV1BlogGet } from '../api/sdk.gen'
import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '../components/ui/card'
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '../components/ui/pagination'
import { Skeleton } from '../components/ui/skeleton'
import type { Route } from './+types/blog'

const PAGE_SIZE = 10

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

export function clientLoader() {
  const blogs = listBlogsApiV1BlogGet({
    baseUrl: import.meta.env.VITE_API_BASE_URL,
  }).then(({ data, error }) => {
    if (error || !data)
      throw new Response('Failed to load archive', { status: 500 })
    return data
  })
  return { blogs }
}

export function HydrateFallback() {
  return (
    <main className="h-full overflow-y-auto px-4 py-12" aria-busy="true">
      <div className="mx-auto max-w-3xl">
        <h1 className="mb-8 text-2xl font-bold text-foreground">アーカイブ</h1>
        <BlogArchiveListSkeleton />
      </div>
    </main>
  )
}

function BlogArchiveListSkeleton() {
  return (
    <ul className="flex flex-col gap-4">
      {Array.from({ length: 4 }, (_, i) => (
        <li key={i}>
          <BlogArchiveCardSkeleton />
        </li>
      ))}
    </ul>
  )
}

function BlogPagination({
  currentPage,
  totalPages,
}: {
  currentPage: number
  totalPages: number
}) {
  if (totalPages <= 1) return null

  const pageUrl = (page: number) => `?page=${page}`

  const pages: (number | 'ellipsis')[] = []
  if (totalPages <= 7) {
    for (let i = 1; i <= totalPages; i++) pages.push(i)
  } else {
    pages.push(1)
    if (currentPage > 3) pages.push('ellipsis')
    for (
      let i = Math.max(2, currentPage - 1);
      i <= Math.min(totalPages - 1, currentPage + 1);
      i++
    ) {
      pages.push(i)
    }
    if (currentPage < totalPages - 2) pages.push('ellipsis')
    pages.push(totalPages)
  }

  return (
    <Pagination className="mt-8">
      <PaginationContent>
        <PaginationItem>
          <PaginationPrevious
            href={currentPage > 1 ? pageUrl(currentPage - 1) : undefined}
            aria-disabled={currentPage <= 1}
            className={currentPage <= 1 ? 'pointer-events-none opacity-50' : ''}
          />
        </PaginationItem>
        {pages.map((page, i) =>
          page === 'ellipsis' ? (
            <PaginationItem key={`ellipsis-${i}`}>
              <PaginationEllipsis />
            </PaginationItem>
          ) : (
            <PaginationItem key={page}>
              <PaginationLink href={pageUrl(page)} isActive={page === currentPage}>
                {page}
              </PaginationLink>
            </PaginationItem>
          ),
        )}
        <PaginationItem>
          <PaginationNext
            href={currentPage < totalPages ? pageUrl(currentPage + 1) : undefined}
            aria-disabled={currentPage >= totalPages}
            className={
              currentPage >= totalPages ? 'pointer-events-none opacity-50' : ''
            }
          />
        </PaginationItem>
      </PaginationContent>
    </Pagination>
  )
}

export default function BlogList({ loaderData }: Route.ComponentProps) {
  const [searchParams] = useSearchParams()
  const currentPage = Math.max(1, Number(searchParams.get('page') ?? '1'))

  return (
    <main className="h-full overflow-y-auto px-4 py-12">
      <div className="mx-auto max-w-3xl">
        <h1 className="mb-8 text-2xl font-bold text-foreground">アーカイブ</h1>
        <Suspense fallback={<BlogArchiveListSkeleton />}>
          <Await resolve={loaderData.blogs}>
            {blogs => {
              if (blogs.length === 0) {
                return (
                  <p className="text-muted-foreground">
                    まだブログ記事がありません。
                  </p>
                )
              }

              const totalPages = Math.ceil(blogs.length / PAGE_SIZE)
              const page = Math.min(currentPage, totalPages)
              const pagedBlogs = blogs.slice(
                (page - 1) * PAGE_SIZE,
                page * PAGE_SIZE,
              )

              return (
                <>
                  <ul className="flex flex-col gap-4">
                    {pagedBlogs.map(post => (
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
                              {new Date(post.created_at).toLocaleDateString(
                                'ja-JP',
                              )}
                            </span>
                          </div>
                        </Link>
                      </li>
                    ))}
                  </ul>
                  <BlogPagination currentPage={page} totalPages={totalPages} />
                </>
              )
            }}
          </Await>
        </Suspense>
      </div>
    </main>
  )
}
