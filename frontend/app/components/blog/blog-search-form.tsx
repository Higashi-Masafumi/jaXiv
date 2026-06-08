import { SearchIcon, XIcon } from 'lucide-react'
import { useNavigate, useSearchParams } from 'react-router'

import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'

export function BlogSearchForm() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const currentKeyword = searchParams.get('keyword')?.trim() ?? ''

  function navigateWithKeyword(keyword: string) {
    const params = new URLSearchParams()
    // Preserve the page size but reset to the first page on a new search.
    const pageSize = searchParams.get('page_size')
    if (pageSize) params.set('page_size', pageSize)
    if (keyword) params.set('keyword', keyword)
    navigate(`?${params}`)
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const value = new FormData(event.currentTarget).get('keyword')
    navigateWithKeyword(typeof value === 'string' ? value.trim() : '')
  }

  return (
    <form
      onSubmit={handleSubmit}
      role="search"
      className="mb-8 flex items-center gap-2"
    >
      <div className="relative flex-1">
        <SearchIcon
          aria-hidden
          className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
        />
        <Input
          key={currentKeyword}
          type="search"
          name="keyword"
          defaultValue={currentKeyword}
          placeholder="タイトル・概要・著者で検索"
          aria-label="ブログ記事を検索"
          className="pl-9"
        />
      </div>
      {currentKeyword && (
        <Button
          type="button"
          variant="ghost"
          onClick={() => navigateWithKeyword('')}
        >
          <XIcon className="size-4" />
          クリア
        </Button>
      )}
      <Button type="submit">検索</Button>
    </form>
  )
}
