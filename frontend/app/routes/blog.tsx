import { Suspense } from 'react'
import { Await } from 'react-router'

import { listBlogsApiV1BlogGet } from '~/api/sdk.gen'
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
    <main className="h-full overflow-y-auto px-4 py-12" aria-busy="true">
      <div className="mx-auto max-w-3xl">
        <h1 className="mb-8 text-2xl font-bold text-foreground">アーカイブ</h1>
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
    return (
      <p className="text-muted-foreground">
        {keyword
          ? `「${keyword}」に一致するブログ記事が見つかりませんでした。`
          : 'まだブログ記事がありません。'}
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
        keyword={keyword}
      />
    </>
  )
}

export default function BlogList({ loaderData }: Route.ComponentProps) {
  return (
    <main className="h-full overflow-y-auto px-4 py-12">
      <div className="mx-auto max-w-3xl">
        <h1 className="mb-8 text-2xl font-bold text-foreground">アーカイブ</h1>
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
