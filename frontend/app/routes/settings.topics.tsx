import { useActionState, useCallback, useEffect, useState } from 'react'
import { XIcon } from 'lucide-react'

import {
  getMyTopicSubscriptionApiV1SubscriptionsMeGet,
  upsertMyTopicSubscriptionApiV1SubscriptionsMePut,
} from '~/api/sdk.gen'
import { useAuth } from '~/contexts/auth-context'
import { Badge } from '~/components/ui/badge'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { PageHeader } from '~/components/page-header'

export function meta() {
  return [
    { title: 'トピック設定 | jaXiv' },
    {
      name: 'description',
      content:
        '興味のあるキーワードを設定して、おすすめの論文ブログを週に1度メールで受け取ります。',
    },
  ]
}

type SaveStatus = 'idle' | 'success' | 'error'

const MAX_KEYWORDS = 20

const PAGE_CLASS = 'h-full overflow-y-auto px-4 pb-10 pt-12 sm:px-6 sm:py-10'
const DESCRIPTION =
  '興味のあるキーワードを登録すると、条件に合うおすすめ論文のブログを週に1度、ログイン中のメールアドレス宛にお届けします。'

export default function SettingsTopics() {
  const { session, isAnonymous, signInWithGoogle } = useAuth()
  const [keywords, setKeywords] = useState<string[]>([])
  const [draft, setDraft] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (isAnonymous) return
    let active = true
    setLoading(true)
    void getMyTopicSubscriptionApiV1SubscriptionsMeGet({
      throwOnError: false,
    }).then(({ data }) => {
      if (!active) return
      setKeywords(data?.keywords ?? [])
      setLoading(false)
    })
    return () => {
      active = false
    }
  }, [isAnonymous])

  const addKeyword = useCallback(() => {
    const value = draft.trim().toLowerCase()
    if (!value) return
    setKeywords(prev =>
      prev.includes(value) || prev.length >= MAX_KEYWORDS
        ? prev
        : [...prev, value],
    )
    setDraft('')
  }, [draft])

  const removeKeyword = useCallback((value: string) => {
    setKeywords(prev => prev.filter(keyword => keyword !== value))
  }, [])

  const [saveStatus, saveAction, isSaving] = useActionState<SaveStatus>(
    async () => {
      const { data, error } =
        await upsertMyTopicSubscriptionApiV1SubscriptionsMePut({
          body: { keywords },
          throwOnError: false,
        })
      if (error || !data) return 'error'
      setKeywords(data.keywords)
      return 'success'
    },
    'idle',
  )

  // Auth is still initializing (the context always resolves to an anon or real session).
  if (session === null) {
    return (
      <main className={PAGE_CLASS} aria-busy="true">
        <div className="mx-auto max-w-2xl">
          <PageHeader title="トピック設定" description={DESCRIPTION} />
          <p className="text-sm text-muted-foreground">読み込み中…</p>
        </div>
      </main>
    )
  }

  if (isAnonymous) {
    return (
      <main className={PAGE_CLASS}>
        <div className="mx-auto max-w-2xl">
          <PageHeader title="トピック設定" description={DESCRIPTION} />
          <div className="rounded-2xl border border-border/80 bg-card p-8 text-center shadow-sm">
            <p className="text-sm text-muted-foreground">
              この機能を使うには Google でログインしてください。
            </p>
            <Button className="mt-5" onClick={signInWithGoogle}>
              Google でログイン
            </Button>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className={PAGE_CLASS}>
      <div className="mx-auto max-w-2xl">
        <PageHeader title="トピック設定" description={DESCRIPTION} />
        <form
          action={saveAction}
          className="rounded-2xl border border-border/80 bg-card p-6 shadow-sm"
        >
          <label htmlFor="keyword-input" className="text-sm font-medium">
            キーワード
          </label>
          <p className="mt-1 text-xs text-muted-foreground">
            例: diffusion model / LLM / reinforcement learning（最大{' '}
            {MAX_KEYWORDS} 件）
          </p>
          <div className="mt-3 flex gap-2">
            <Input
              id="keyword-input"
              value={draft}
              onChange={event => setDraft(event.target.value)}
              onKeyDown={event => {
                if (event.key === 'Enter') {
                  event.preventDefault()
                  addKeyword()
                }
              }}
              placeholder="キーワードを入力して Enter"
              disabled={loading}
            />
            <Button
              type="button"
              variant="secondary"
              onClick={addKeyword}
              disabled={loading}
            >
              追加
            </Button>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {keywords.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                まだキーワードがありません。
              </p>
            ) : (
              keywords.map(keyword => (
                <Badge
                  key={keyword}
                  variant="secondary"
                  className="gap-1 py-1 pl-3 pr-1.5 text-sm font-normal"
                >
                  {keyword}
                  <button
                    type="button"
                    onClick={() => removeKeyword(keyword)}
                    aria-label={`${keyword} を削除`}
                    className="rounded-full p-0.5 text-muted-foreground hover:bg-foreground/10 hover:text-foreground"
                  >
                    <XIcon className="size-3.5" />
                  </button>
                </Badge>
              ))
            )}
          </div>

          <div className="mt-6 flex items-center gap-3">
            <Button type="submit" disabled={isSaving || loading}>
              {isSaving ? '保存中…' : '保存する'}
            </Button>
            {saveStatus === 'success' && (
              <span className="text-sm text-muted-foreground">
                保存しました
              </span>
            )}
            {saveStatus === 'error' && (
              <span className="text-sm text-destructive">
                保存に失敗しました
              </span>
            )}
          </div>

          <p className="mt-4 text-xs text-muted-foreground">
            キーワードを空のまま保存すると、配信は行われません。
          </p>
        </form>
      </div>
    </main>
  )
}
