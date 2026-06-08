import { useEffect, useRef } from 'react'
import { LoaderCircleIcon, SearchIcon, XIcon } from 'lucide-react'
import { Form, useNavigation, useSearchParams, useSubmit } from 'react-router'

import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'

// Wait a beat after the last keystroke before hitting the loader, so live
// filtering doesn't fire a request on every character.
const DEBOUNCE_MS = 300

/**
 * Keyword search for the public blog archive.
 *
 * Follows the React Router data pattern for search/filter UIs: a GET `<Form>`
 * serialises its fields into the URL and re-runs the route loader (searching is
 * a read, so it belongs in the loader, not an action). `useSubmit` drives
 * debounced live filtering, and the input value stays in sync with the URL so
 * browser back/forward keeps working.
 */
export function BlogSearchForm() {
  const [searchParams] = useSearchParams()
  const submit = useSubmit()
  const navigation = useNavigation()

  const keyword = searchParams.get('keyword') ?? ''
  // Preserve the chosen page size across searches (reset to page 1 implicitly,
  // since `page` is not part of this form).
  const pageSize = searchParams.get('page_size') ?? ''

  // A keyword navigation is in flight. For GET submissions the pending data
  // lives in `navigation.location.search`, not `navigation.formData`.
  const searching =
    navigation.location != null &&
    new URLSearchParams(navigation.location.search).has('keyword')

  // Keep the uncontrolled input in sync with the URL (e.g. on back/forward).
  const inputRef = useRef<HTMLInputElement>(null)
  useEffect(() => {
    if (inputRef.current) inputRef.current.value = keyword
  }, [keyword])

  const timerRef = useRef<ReturnType<typeof setTimeout>>(undefined)
  function handleChange(event: React.FormEvent<HTMLFormElement>) {
    const form = event.currentTarget
    // Push a history entry for the first search, then replace it on subsequent
    // keystrokes so the back button returns to the unfiltered list in one step.
    const isFirstSearch = keyword === ''
    clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => {
      submit(form, { replace: !isFirstSearch })
    }, DEBOUNCE_MS)
  }

  function handleClear() {
    if (inputRef.current) inputRef.current.value = ''
    clearTimeout(timerRef.current)
    inputRef.current?.form?.requestSubmit()
  }

  return (
    <Form
      method="get"
      role="search"
      onChange={handleChange}
      onSubmit={() => clearTimeout(timerRef.current)}
      className="mb-8 flex items-center gap-2"
    >
      {pageSize && <input type="hidden" name="page_size" value={pageSize} />}
      <div className="relative flex-1">
        {searching ? (
          <LoaderCircleIcon
            aria-hidden
            className="absolute top-1/2 left-3 size-4 -translate-y-1/2 animate-spin text-muted-foreground"
          />
        ) : (
          <SearchIcon
            aria-hidden
            className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
          />
        )}
        <Input
          ref={inputRef}
          type="search"
          name="keyword"
          defaultValue={keyword}
          placeholder="タイトル・概要・著者で検索"
          aria-label="ブログ記事を検索"
          className="pl-9"
        />
      </div>
      {keyword && (
        <Button type="button" variant="ghost" onClick={handleClear}>
          <XIcon className="size-4" />
          クリア
        </Button>
      )}
    </Form>
  )
}
