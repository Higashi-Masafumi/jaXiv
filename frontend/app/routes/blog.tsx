import { Link } from 'react-router'
import { ArchiveIcon, SearchXIcon } from 'lucide-react'

import { listBlogsApiV1BlogGet } from '~/api/sdk.gen'
import { Button } from '~/components/ui/button'
import { EmptyState } from '~/components/empty-state'
import { PageHeader } from '~/components/page-header'
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

// 記事一覧（公開）。サーバーサイドで取得して初期HTMLに各記事への内部リンクと
// タイトルを含めることで、クローラが記事ページを辿れるようにする（公開APIなので
// 認証不要、baseUrlを明示）。
export async function loader({ request }: Route.LoaderArgs) {
  const { page, pageSize, keyword } = parsePageParams(new URL(request.url))

  const { data, error } = await listBlogsApiV1BlogGet({
    baseUrl: import.meta.env.VITE_API_BASE_URL,
    query: { page, page_size: pageSize, keyword },
    throwOnError: false,
  })
  if (error || !data)
    throw new Response('Failed to load archive', { status: 500 })

  return { blogs: data, keyword }
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
        <BlogPostList data={loaderData.blogs} keyword={loaderData.keyword} />
      </div>
    </main>
  )
}
