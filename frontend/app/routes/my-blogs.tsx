import { Suspense } from 'react'
import { Await, Link } from 'react-router'
import { FileTextIcon } from 'lucide-react'

import { listMyBlogsApiV1BlogMyGet } from '~/api/sdk.gen'
import type { PaginatedBlogPostResponseSchema } from '~/api/types.gen'
import { Button } from '~/components/ui/button'
import { EmptyState } from '~/components/empty-state'
import { PageHeader } from '~/components/page-header'
import { BlogListSkeleton } from '~/components/blog/blog-card-skeleton'
import {
  BlogListPagination,
  parsePageParams,
} from '~/components/blog/blog-list-pagination'
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
      <EmptyState
        icon={FileTextIcon}
        title="まだPDF生成ブログがありません"
        description="PDF をアップロードして、最初のブログ記事を生成しましょう。"
        action={
          <Button asChild>
            <Link to="/pdf">PDFから生成する</Link>
          </Button>
        }
      />
    )
  }
  return (
    <>
      <ul className="grid gap-3 sm:grid-cols-2">
        {data.items.map(post => (
          <li key={post.paper_id}>
            <BlogPostCard post={post} showPaperId={false} />
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
    <main
      className="h-full overflow-y-auto px-4 pb-10 pt-12 sm:px-6 sm:py-10"
      aria-busy="true"
    >
      <div className="mx-auto max-w-4xl">
        <PageHeader
          title="マイブログ"
          description="あなたが PDF から生成したブログ記事の一覧です。"
        />
        <BlogListSkeleton />
      </div>
    </main>
  )
}

export default function MyBlogs({ loaderData }: Route.ComponentProps) {
  return (
    <main className="h-full overflow-y-auto px-4 pb-10 pt-12 sm:px-6 sm:py-10">
      <div className="mx-auto max-w-4xl">
        <PageHeader
          title="マイブログ"
          description="あなたが PDF から生成したブログ記事の一覧です。"
        />
        <Suspense fallback={<BlogListSkeleton />}>
          <Await resolve={loaderData.blogs}>
            {data => <BlogPostList data={data} />}
          </Await>
        </Suspense>
      </div>
    </main>
  )
}
