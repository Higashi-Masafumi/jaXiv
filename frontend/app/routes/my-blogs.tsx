import { Suspense, useEffect } from 'react'
import { Await, Link, useNavigate } from 'react-router'

import { useAuth } from '~/contexts/auth-context'
import { listMyBlogsApiV1BlogMyGet } from '~/api/sdk.gen'
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
import type { PaginatedBlogPostResponseSchema } from '../api/types.gen'
import type { Route } from './+types/my-blogs'

const PAGE_SIZE = 10

export function meta() {
  return [
    { title: 'マイブログ | jaXiv' },
    { name: 'description', content: '自分のPDF生成ブログ一覧' },
  ]
}

async function fetchMyBlogs(
  page: number,
  pageSize: number,
): Promise<PaginatedBlogPostResponseSchema> {
  const { data, error } = await listMyBlogsApiV1BlogMyGet({
    query: { page, page_size: pageSize },
    throwOnError: false,
  })
  if (error || !data)
    throw new Response('Failed to load my blogs', { status: 500 })
  return data
}

function BlogCardSkeleton() {
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

function ListSkeleton() {
  return (
    <ul className="flex flex-col gap-4">
      {Array.from({ length: 3 }, (_, i) => (
        <li key={i}>
          <BlogCardSkeleton />
        </li>
      ))}
    </ul>
  )
}

function buildPages(
  currentPage: number,
  totalPages: number,
): (number | 'ellipsis')[] {
  const left = Math.max(2, currentPage - 1)
  const right = Math.min(totalPages - 1, currentPage + 1)
  const middle = Array.from({ length: right - left + 1 }, (_, i) => left + i)
  return [
    1,
    ...(left > 2 ? (['ellipsis'] as const) : []),
    ...middle,
    ...(right < totalPages - 1 ? (['ellipsis'] as const) : []),
    totalPages,
  ]
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
  const pages = buildPages(currentPage, totalPages)

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
              <PaginationLink
                href={pageUrl(page)}
                isActive={page === currentPage}
              >
                {page}
              </PaginationLink>
            </PaginationItem>
          ),
        )}
        <PaginationItem>
          <PaginationNext
            href={
              currentPage < totalPages ? pageUrl(currentPage + 1) : undefined
            }
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

function BlogPostList({ data }: { data: PaginatedBlogPostResponseSchema }) {
  if (data.items.length === 0) {
    return (
      <p className="text-muted-foreground">
        まだPDF生成ブログがありません。{' '}
        <Link to="/pdf" className="underline underline-offset-2">
          PDFからブログを生成
        </Link>{' '}
        してみましょう。
      </p>
    )
  }
  return (
    <>
      <ul className="flex flex-col gap-4">
        {data.items.map(post => (
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
      <BlogPagination currentPage={data.page} totalPages={data.total_pages} />
    </>
  )
}

export function clientLoader({ request }: Route.ClientLoaderArgs) {
  const url = new URL(request.url)
  const page = Math.max(1, Number(url.searchParams.get('page') ?? '1'))
  const blogs = fetchMyBlogs(page, PAGE_SIZE)
  return { blogs }
}

export function HydrateFallback() {
  return (
    <main className="h-full overflow-y-auto px-4 py-12" aria-busy="true">
      <div className="mx-auto max-w-3xl">
        <h1 className="mb-8 text-2xl font-bold text-foreground">マイブログ</h1>
        <ListSkeleton />
      </div>
    </main>
  )
}

export default function MyBlogs({ loaderData }: Route.ComponentProps) {
  const { user, isAnonymous } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (user !== null && isAnonymous) {
      navigate('/login', { replace: true })
    }
  }, [user, isAnonymous, navigate])

  return (
    <main className="h-full overflow-y-auto px-4 py-12">
      <div className="mx-auto max-w-3xl">
        <h1 className="mb-8 text-2xl font-bold text-foreground">マイブログ</h1>
        <Suspense fallback={<ListSkeleton />}>
          <Await resolve={loaderData.blogs}>
            {data => <BlogPostList data={data} />}
          </Await>
        </Suspense>
      </div>
    </main>
  )
}
