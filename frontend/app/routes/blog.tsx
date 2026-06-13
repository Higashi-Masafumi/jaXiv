import { Suspense } from 'react'
import { Await, Link } from 'react-router'
import { ArchiveIcon, SearchXIcon } from 'lucide-react'

import { listBlogsApiV1BlogGet } from '~/api/sdk.gen'
import { Button } from '~/components/ui/button'
import { EmptyState } from '~/components/empty-state'
import { PageHeader } from '~/components/page-header'
import { BlogListSkeleton } from '~/components/blog/blog-card-skeleton'
import {
  BlogListPagination,
  parsePageParams,
} from '~/components/blog/blog-list-pagination'
import { BlogPostCard } from '~/components/blog/blog-post-card'
import { BlogSearchForm } from '~/components/blog/blog-search-form'
import type { PaginatedBlogPostResponseSchema } from '~/api/types.gen'
import type { Route } from './+types/blog'

export function meta() {
  return [
    { title: 'アーカイブ | jaXiv' },
    { name: 'description', content: '生成済みのブログ記事一覧' },
  ]
}

export function clientLoader({ request }: Route.ClientLoaderArgs) {
  const { page, pageSize, keyword } = parsePageParams(new URL(request.url))

  const blogs = listBlogsApiV1BlogGet({
    baseUrl: import.meta.env.VITE_API_BASE_URL,
    query: { page, page_size: pageSize, keyword },
  }).then(({ data, error }) => {
    if (error || !data)
      throw new Response('Failed to load archive', { status: 500 })
    return data
  })
  return { blogs, keyword }
}

export function HydrateFallback() {
  return (
    <main
      className="h-full overflow-y-auto px-4 pb-10 pt-12 sm:px-6 sm:py-10"
      aria-busy="true"
    >
      <div className="mx-auto max-w-4xl">
        <PageHeader
          title="アーカイブ"
          description="生成されたブログ記事を検索して閲覧できます。"
        />
        <BlogSearchForm />
        <BlogListSkeleton count={4} />
      </div>
    </main>
  )
}

function BlogPostList({
  data,
  keyword,
}: {
  data: PaginatedBlogPostResponseSchema
  keyword?: string
}) {
  if (data.items.length === 0) {
    if (keyword) {
      return (
        <EmptyState
          icon={SearchXIcon}
          title={`「${keyword}」に一致する記事が見つかりませんでした`}
          description="別のキーワードでもう一度お試しください。"
        />
      )
    }
    return (
      <EmptyState
        icon={ArchiveIcon}
        title="まだブログ記事がありません"
        description="arXiv ID を入力すると、論文から読みやすいブログ記事を生成できます。"
        action={
          <Button asChild>
            <Link to="/">arXiv から生成する</Link>
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
            <BlogPostCard post={post} />
          </li>
        ))}
      </ul>
      <BlogListPagination
        currentPage={data.page}
        totalPages={data.total_pages}
        pageSize={data.page_size}
        keyword={keyword}
      />
    </>
  )
}

export default function BlogList({ loaderData }: Route.ComponentProps) {
  return (
    <main className="h-full overflow-y-auto px-4 pb-10 pt-12 sm:px-6 sm:py-10">
      <div className="mx-auto max-w-4xl">
        <PageHeader
          title="アーカイブ"
          description="生成されたブログ記事を検索して閲覧できます。"
        />
        <BlogSearchForm />
        <Suspense fallback={<BlogListSkeleton count={4} />}>
          <Await resolve={loaderData.blogs}>
            {data => <BlogPostList data={data} keyword={loaderData.keyword} />}
          </Await>
        </Suspense>
      </div>
    </main>
  )
}
