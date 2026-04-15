import { useEffect } from 'react'
import { useNavigate } from 'react-router'
import { useAuth } from '~/contexts/auth-context'
import { Button } from '~/components/ui/button'

export function meta() {
  return [
    { title: 'ログイン | jaXiv' },
    { name: 'description', content: 'jaXivにログインします。' },
  ]
}

export default function Login() {
  const { user, isAnonymous, signInWithGoogle } = useAuth()
  const navigate = useNavigate()

  // Already logged in as a real user → redirect home
  useEffect(() => {
    if (user && !isAnonymous) {
      navigate('/', { replace: true })
    }
  }, [user, isAnonymous, navigate])

  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-8 bg-hero-background px-4 text-hero-foreground">
      <div className="space-y-2 text-center">
        <h1 className="text-4xl font-black tracking-tight">jaXiv</h1>
        <p className="text-base text-hero-muted">
          ログインしてPDF論文からブログを生成しましょう。
        </p>
      </div>
      <div className="w-full max-w-sm rounded-2xl border border-hero-card-border/70 bg-hero-card/80 p-6 shadow-2xl backdrop-blur-sm">
        <Button
          onClick={signInWithGoogle}
          className="w-full bg-hero-accent font-semibold text-primary-foreground hover:bg-hero-accent/90"
        >
          Googleでログイン
        </Button>
      </div>
    </main>
  )
}
