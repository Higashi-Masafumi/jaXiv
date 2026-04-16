import { useNavigate } from 'react-router'

import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '~/components/ui/pagination'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select'
import { cn } from '~/lib/utils'

const PAGE_SIZE_OPTIONS = [10, 20, 50] as const
const DEFAULT_PAGE_SIZE = 10

export function parsePageParams(url: URL): {
  page: number
  pageSize: number
} {
  const page = Math.max(1, Number(url.searchParams.get('page') ?? '1'))
  const raw = Number(url.searchParams.get('page_size'))
  const pageSize = (PAGE_SIZE_OPTIONS as readonly number[]).includes(raw)
    ? raw
    : DEFAULT_PAGE_SIZE
  return { page, pageSize }
}

function buildPageUrl(page: number, pageSize: number): string {
  const params = new URLSearchParams()
  params.set('page', String(page))
  if (pageSize !== DEFAULT_PAGE_SIZE) params.set('page_size', String(pageSize))
  return `?${params}`
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

export function BlogListPagination({
  currentPage,
  totalPages,
  pageSize,
}: {
  currentPage: number
  totalPages: number
  pageSize: number
}) {
  const navigate = useNavigate()

  if (totalPages <= 1 && pageSize === DEFAULT_PAGE_SIZE) return null

  const pages = totalPages > 1 ? buildPages(currentPage, totalPages) : []

  return (
    <div className="mt-8 flex flex-col items-center gap-4 sm:flex-row sm:justify-between">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <span>表示件数</span>
        <Select
          value={String(pageSize)}
          onValueChange={v => navigate(buildPageUrl(1, Number(v)))}
        >
          <SelectTrigger className="w-20">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {PAGE_SIZE_OPTIONS.map(size => (
              <SelectItem key={size} value={String(size)}>
                {size}件
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {totalPages > 1 && (
        <Pagination className="mx-0 w-auto">
          <PaginationContent>
            <PaginationItem>
              <PaginationPrevious
                href={
                  currentPage > 1
                    ? buildPageUrl(currentPage - 1, pageSize)
                    : undefined
                }
                aria-disabled={currentPage <= 1}
                className={cn(
                  currentPage <= 1 && 'pointer-events-none opacity-50',
                )}
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
                    href={buildPageUrl(page, pageSize)}
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
                  currentPage < totalPages
                    ? buildPageUrl(currentPage + 1, pageSize)
                    : undefined
                }
                aria-disabled={currentPage >= totalPages}
                className={cn(
                  currentPage >= totalPages &&
                    'pointer-events-none opacity-50',
                )}
              />
            </PaginationItem>
          </PaginationContent>
        </Pagination>
      )}
    </div>
  )
}
