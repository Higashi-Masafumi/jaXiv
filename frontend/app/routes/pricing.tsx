import { useState } from 'react'
import { Link, useNavigate } from 'react-router'

import {
  createCheckoutSessionApiV1BillingCheckoutSessionPost,
  createPortalSessionApiV1BillingPortalSessionPost,
} from '~/api/sdk.gen'
import { Button } from '~/components/ui/button'
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
    <main className="mx-auto w-full max-w-4xl px-6 py-12">
      <div className="mb-10 text-center">
        <h1 className="text-3xl font-bold tracking-tight">料金プラン</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          無料でも使えますが、ヘビーユーザー向けに有料プランをご用意しています。
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <PlanCard
          name="Free"
          price="¥0"
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
          price="¥980 / 月"
          highlight
          features={['ブログ生成: 月100回', 'チャット: 無制限', '優先サポート']}
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
                className="w-full"
              >
                {pending === 'checkout'
                  ? 'Stripe に移動中…'
                  : isAnonymous
                    ? 'Googleでログインして開始'
                    : '有料プランにアップグレード'}
              </Button>
            )
          }
        />
      </div>

      <div className="mt-10 text-center text-xs text-muted-foreground">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="underline underline-offset-2"
        >
          もどる
        </button>
        ・
        <Link to="/" className="underline underline-offset-2">
          ホームへ
        </Link>
      </div>
    </main>
  )
}

function PlanCard(props: {
  name: string
  price: string
  features: string[]
  cta: React.ReactNode
  highlight?: boolean
}) {
  const { name, price, features, cta, highlight } = props
  return (
    <div
      className={
        'rounded-2xl border p-6 ' +
        (highlight
          ? 'border-hero-accent bg-hero-accent/5 shadow-lg'
          : 'border-border bg-card')
      }
    >
      <div className="mb-4">
        <p className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          {name}
        </p>
        <p className="mt-1 text-3xl font-bold">{price}</p>
      </div>
      <ul className="mb-6 space-y-2 text-sm">
        {features.map(f => (
          <li key={f} className="flex items-start gap-2">
            <span className="text-hero-accent">✓</span>
            <span>{f}</span>
          </li>
        ))}
      </ul>
      {cta}
    </div>
  )
}
