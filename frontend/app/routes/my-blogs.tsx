import { Suspense } from 'react'
import { Await, Link } from 'react-router'

import { listMyBlogsApiV1BlogMyGet } from '~/api/sdk.gen'
import type { PaginatedBlogPostResponseSchema } from '~/api/types.gen'
import { BlogListSkeleton } from '~/components/blog/blog-card-skeleton'
import { BlogListPagination, parsePageParams } from '~/components/blog/blog-list-pagination'
import { BlogPostCard } from '~/components/blog/blog-post-card'
import type { Route } from './+types/my-blogs'

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
  if (error || !data) {
    return { items: [], total: 0, page: 1, page_size: pageSize, total_pages: 0 }
  }
  return data
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
            <BlogPostCard post={post} />
          </li>
        ))}
      </ul>
      <BlogListPagination
        currentPage={data.page}
        totalPages={data.total_pages}
        pageSize={data.page_size}
      />
    </>
  )
}

export function clientLoader({ request }: Route.ClientLoaderArgs) {
  const { page, pageSize } = parsePageParams(new URL(request.url))
  const blogs = fetchMyBlogs(page, pageSize)
  return { blogs }
}

export function HydrateFallback() {
  return (
    <main className="h-full overflow-y-auto px-4 py-12" aria-busy="true">
      <div className="mx-auto max-w-3xl">
        <h1 className="mb-8 text-2xl font-bold text-foreground">マイブログ</h1>
        <BlogListSkeleton />
      </div>
    </main>
  )
}

export default function MyBlogs({ loaderData }: Route.ComponentProps) {
  return (
    <main className="h-full overflow-y-auto px-4 py-12">
      <div className="mx-auto max-w-3xl">
        <h1 className="mb-8 text-2xl font-bold text-foreground">マイブログ</h1>
        <Suspense fallback={<BlogListSkeleton />}>
          <Await resolve={loaderData.blogs}>
            {data => <BlogPostList data={data} />}
          </Await>
        </Suspense>
      </div>
    </main>
  )
}
