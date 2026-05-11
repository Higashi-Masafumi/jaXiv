import { Link } from 'react-router'

import { Button } from '~/components/ui/button'

export function meta() {
  return [{ title: '決済キャンセル | jaXiv' }]
}

export default function BillingCancel() {
  return (
    <main className="mx-auto flex min-h-[60vh] max-w-md flex-col items-center justify-center gap-6 px-6 py-12 text-center">
      <h1 className="text-2xl font-bold">決済はキャンセルされました</h1>
      <p className="text-sm text-muted-foreground">
        決済処理は完了していません。プランは変更されていません。
      </p>
      <Button asChild>
        <Link to="/pricing">料金プランに戻る</Link>
      </Button>
    </main>
  )
}
