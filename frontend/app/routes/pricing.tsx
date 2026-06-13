import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { CheckIcon, CrownIcon, ZapIcon } from 'lucide-react'

import {
  createCheckoutSessionApiV1BillingCheckoutSessionPost,
  createPortalSessionApiV1BillingPortalSessionPost,
} from '~/api/sdk.gen'
import { Button } from '~/components/ui/button'
import { PageHeader } from '~/components/page-header'
import { useAuth } from '~/contexts/auth-context'

export function meta() {
  return [
    { title: '料金プラン | jaXiv' },
    {
      name: 'description',
      content: 'jaXiv の料金プランと有料プランへのアップグレード。',
    },
  ]
}

export default function Pricing() {
  const { isAnonymous, isPaid, signInWithGoogle } = useAuth()
  const [pending, setPending] = useState<'checkout' | 'portal' | null>(null)
  const navigate = useNavigate()

  const handleUpgrade = async () => {
    if (isAnonymous) {
      await signInWithGoogle()
      return
    }
    setPending('checkout')
    const { data } =
      await createCheckoutSessionApiV1BillingCheckoutSessionPost()
    setPending(null)
    if (data?.url) {
      window.location.href = data.url
    }
  }

  const handleManage = async () => {
    setPending('portal')
    const { data } = await createPortalSessionApiV1BillingPortalSessionPost()
    setPending(null)
    if (data?.url) {
      window.location.href = data.url
    }
  }

  return (
    <main className="h-full overflow-y-auto px-4 pb-12 pt-12 sm:px-6 sm:pt-10">
      <div className="mx-auto w-full max-w-3xl">
        <PageHeader
          title="料金プラン"
          description="無料でも十分使えますが、もっと活用したい方向けに有料プランをご用意しています。"
        />

        <div className="grid gap-4 sm:grid-cols-2">
          <PlanCard
            name="Free"
            price="¥0"
            period="ずっと無料"
            features={[
              'ブログ生成: 月10回',
              'チャット: 1日30メッセージ',
              'arXiv 論文の翻訳・閲覧',
            ]}
            cta={
              isPaid ? (
                <Button variant="outline" className="w-full" disabled>
                  現在のプランより下位
                </Button>
              ) : (
                <Button variant="outline" className="w-full" disabled>
                  利用中
                </Button>
              )
            }
          />
          <PlanCard
            name="Paid"
            price="¥500"
            period="/ 月"
            highlight
            icon={<CrownIcon className="size-4" />}
            features={[
              'ブログ生成: 月100回',
              'チャット: 無制限',
              '優先サポート',
            ]}
            cta={
              isPaid ? (
                <Button
                  onClick={handleManage}
                  disabled={pending !== null}
                  className="w-full"
                >
                  {pending === 'portal' ? '読み込み中…' : '請求情報を管理'}
                </Button>
              ) : (
                <Button
                  onClick={handleUpgrade}
                  disabled={pending !== null}
                  className="w-full gap-2"
                >
                  {pending === 'checkout' ? (
                    <>
                      <span className="inline-block size-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                      Stripe に移動中…
                    </>
                  ) : (
                    <>
                      <ZapIcon className="size-4" />
                      {isAnonymous
                        ? 'Googleでログインして開始'
                        : 'アップグレード'}
                    </>
                  )}
                </Button>
              )
            }
          />
        </div>

        <div className="mt-10 text-center text-xs text-muted-foreground">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="underline underline-offset-2 hover:text-foreground transition-colors"
          >
            もどる
          </button>
          <span className="mx-2 opacity-50">·</span>
          <Link
            to="/"
            className="underline underline-offset-2 hover:text-foreground transition-colors"
          >
            ホームへ
          </Link>
        </div>
      </div>
    </main>
  )
}

function PlanCard(props: {
  name: string
  price: string
  period: string
  features: string[]
  cta: React.ReactNode
  highlight?: boolean
  icon?: React.ReactNode
}) {
  const { name, price, period, features, cta, highlight, icon } = props

  return (
    <div
      className={
        'relative flex flex-col rounded-2xl p-6 ' +
        (highlight
          ? 'border-2 border-primary bg-gradient-to-b from-primary/5 to-violet-50/30 shadow-lg shadow-primary/10 dark:from-primary/10 dark:to-primary/5'
          : 'border border-border bg-card shadow-sm')
      }
    >
      {highlight && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <span className="inline-flex items-center gap-1 rounded-full bg-primary px-3 py-0.5 text-xs font-semibold text-primary-foreground shadow-sm">
            おすすめ
          </span>
        </div>
      )}

      <div className="mb-5">
        <div className="mb-3 flex items-center gap-2">
          {icon && (
            <span
              className={highlight ? 'text-primary' : 'text-muted-foreground'}
            >
              {icon}
            </span>
          )}
          <p
            className={`text-xs font-semibold uppercase tracking-widest ${
              highlight ? 'text-primary' : 'text-muted-foreground'
            }`}
          >
            {name}
          </p>
        </div>
        <div className="flex items-end gap-1">
          <span className="text-4xl font-black tracking-tight text-foreground">
            {price}
          </span>
          <span className="mb-0.5 text-sm text-muted-foreground">{period}</span>
        </div>
      </div>

      <ul className="mb-6 flex-1 space-y-3">
        {features.map(f => (
          <li key={f} className="flex items-start gap-2.5">
            <CheckIcon
              className={`mt-0.5 size-4 shrink-0 ${
                highlight ? 'text-primary' : 'text-muted-foreground'
              }`}
            />
            <span className="text-sm text-foreground">{f}</span>
          </li>
        ))}
      </ul>

      {cta}
    </div>
  )
}
