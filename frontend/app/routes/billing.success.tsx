import { useEffect } from 'react'
import { Link } from 'react-router'

import { Button } from '~/components/ui/button'
import { useAuth } from '~/contexts/auth-context'

export function meta() {
  return [{ title: '決済完了 | jaXiv' }]
}

export default function BillingSuccess() {
  const { refreshPlan } = useAuth()

  useEffect(() => {
    // Stripe webhook may take a moment; poll the plan a few times.
    let cancelled = false
    const tick = async (n: number) => {
      if (cancelled) return
      await refreshPlan()
      if (n > 0) {
        setTimeout(() => void tick(n - 1), 1500)
      }
    }
    void tick(3)
    return () => {
      cancelled = true
    }
  }, [refreshPlan])

  return (
    <main className="mx-auto flex min-h-[60vh] max-w-md flex-col items-center justify-center gap-6 px-6 py-12 text-center">
      <h1 className="text-2xl font-bold">ご購入ありがとうございます</h1>
      <p className="text-sm text-muted-foreground">
        有料プランを反映しています。少し時間がかかる場合があります。
      </p>
      <div className="flex gap-3">
        <Button asChild>
          <Link to="/">ホームへ</Link>
        </Button>
        <Button asChild variant="outline">
          <Link to="/pricing">プランを確認</Link>
        </Button>
      </div>
    </main>
  )
}
