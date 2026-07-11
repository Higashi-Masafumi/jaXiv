import {
  useActionState,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react'
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
import { cn } from '~/lib/utils'

export function meta() {
  return [
    { title: 'トピック設定 | jaXiv' },
    {
      name: 'description',
      content:
        '興味のある研究分野を選ぶと、おすすめの論文ブログを週に1度メールで受け取ります。',
    },
  ]
}

type SaveStatus = 'idle' | 'success' | 'error'
type Topic = { label: string; keyword: string }
type TopicGroup = { group: string; topics: Topic[] }

// Suggested research topics. Each maps to an English keyword that actually appears
// in arXiv titles/abstracts, since the backend matches keywords against paper text.
const TOPIC_GROUPS: TopicGroup[] = [
  {
    group: '自然言語処理・LLM',
    topics: [
      { label: '大規模言語モデル (LLM)', keyword: 'language model' },
      { label: 'Transformer', keyword: 'transformer' },
      { label: 'RAG（検索拡張生成）', keyword: 'retrieval-augmented' },
      { label: 'LLMエージェント', keyword: 'llm agent' },
      { label: '機械翻訳', keyword: 'machine translation' },
      { label: '質問応答', keyword: 'question answering' },
    ],
  },
  {
    group: 'コンピュータビジョン',
    topics: [
      { label: '画像認識', keyword: 'image classification' },
      { label: '物体検出', keyword: 'object detection' },
      { label: 'セグメンテーション', keyword: 'segmentation' },
      { label: '動画・映像理解', keyword: 'video' },
      { label: '3D・点群', keyword: 'point cloud' },
    ],
  },
  {
    group: '生成モデル',
    topics: [
      { label: '拡散モデル', keyword: 'diffusion' },
      { label: '画像生成', keyword: 'image generation' },
      { label: '敵対的生成 (GAN)', keyword: 'generative adversarial' },
      { label: '音声合成', keyword: 'speech synthesis' },
    ],
  },
  {
    group: '強化学習・ロボティクス',
    topics: [
      { label: '強化学習', keyword: 'reinforcement learning' },
      { label: 'RLHF・アライメント', keyword: 'rlhf' },
      { label: 'ロボット制御', keyword: 'robot' },
      { label: '自動運転', keyword: 'autonomous driving' },
    ],
  },
  {
    group: '基盤・応用',
    topics: [
      { label: 'マルチモーダル', keyword: 'multimodal' },
      { label: 'グラフニューラルネット', keyword: 'graph neural network' },
      { label: '音声認識', keyword: 'speech recognition' },
      { label: '時系列', keyword: 'time series' },
      { label: '推薦システム', keyword: 'recommendation' },
      { label: '医療・バイオ', keyword: 'medical' },
    ],
  },
]

const ALL_SUGGESTED_KEYWORDS = new Set(
  TOPIC_GROUPS.flatMap(group => group.topics.map(topic => topic.keyword)),
)

const MAX_KEYWORDS = 20
const PAGE_CLASS = 'h-full overflow-y-auto px-4 pb-10 pt-12 sm:px-6 sm:py-10'
const DESCRIPTION =
  '興味のある研究分野を選ぶと、条件に合うおすすめ論文のブログを週に1度、ログイン中のメールアドレス宛にお届けします。'

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

  const toggleKeyword = useCallback((keyword: string) => {
    setKeywords(prev =>
      prev.includes(keyword)
        ? prev.filter(item => item !== keyword)
        : prev.length >= MAX_KEYWORDS
          ? prev
          : [...prev, keyword],
    )
  }, [])

  const addCustom = useCallback(() => {
    const value = draft.trim().toLowerCase()
    if (!value) return
    setKeywords(prev =>
      prev.includes(value) || prev.length >= MAX_KEYWORDS
        ? prev
        : [...prev, value],
    )
    setDraft('')
  }, [draft])

  const removeKeyword = useCallback((keyword: string) => {
    setKeywords(prev => prev.filter(item => item !== keyword))
  }, [])

  const customKeywords = useMemo(
    () => keywords.filter(keyword => !ALL_SUGGESTED_KEYWORDS.has(keyword)),
    [keywords],
  )

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
        <div className="mx-auto max-w-3xl">
          <PageHeader title="トピック設定" description={DESCRIPTION} />
          <p className="text-sm text-muted-foreground">読み込み中…</p>
        </div>
      </main>
    )
  }

  if (isAnonymous) {
    return (
      <main className={PAGE_CLASS}>
        <div className="mx-auto max-w-3xl">
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
      <div className="mx-auto max-w-3xl">
        <PageHeader title="トピック設定" description={DESCRIPTION} />
        <form action={saveAction} className="space-y-8">
          <div className="rounded-2xl border border-border/80 bg-card p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-foreground">
                興味のある分野
              </h2>
              <span className="text-xs text-muted-foreground">
                {keywords.length} 件選択中
              </span>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              タップして選択します。複数選べます。
            </p>

            <div className="mt-4 space-y-5">
              {TOPIC_GROUPS.map(group => (
                <section key={group.group}>
                  <h3 className="text-xs font-medium text-muted-foreground">
                    {group.group}
                  </h3>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {group.topics.map(topic => {
                      const active = keywords.includes(topic.keyword)
                      return (
                        <button
                          key={topic.keyword}
                          type="button"
                          aria-pressed={active}
                          onClick={() => toggleKeyword(topic.keyword)}
                          disabled={loading}
                          className={cn(
                            'rounded-full border px-3 py-1.5 text-sm transition-colors',
                            active
                              ? 'border-primary bg-primary text-primary-foreground'
                              : 'border-border bg-background text-foreground hover:bg-muted',
                          )}
                        >
                          {topic.label}
                        </button>
                      )
                    })}
                  </div>
                </section>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-border/80 bg-card p-6 shadow-sm">
            <h2 className="text-sm font-semibold text-foreground">
              自由キーワード
            </h2>
            <p className="mt-1 text-xs text-muted-foreground">
              上の候補にない語で絞り込めます。論文のタイトル・要約（英語）に含まれる語でマッチするため、英語での入力を推奨します。
            </p>
            <div className="mt-3 flex gap-2">
              <Input
                id="keyword-input"
                value={draft}
                onChange={event => setDraft(event.target.value)}
                onKeyDown={event => {
                  if (event.key === 'Enter') {
                    event.preventDefault()
                    addCustom()
                  }
                }}
                placeholder="例: mixture of experts"
                disabled={loading}
              />
              <Button
                type="button"
                variant="secondary"
                onClick={addCustom}
                disabled={loading}
              >
                追加
              </Button>
            </div>
            {customKeywords.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {customKeywords.map(keyword => (
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
                ))}
              </div>
            )}
          </div>

          <div className="flex items-center gap-3">
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
            <span className="ml-auto text-xs text-muted-foreground">
              未選択のまま保存すると配信は行われません
            </span>
          </div>
        </form>
      </div>
    </main>
  )
}
