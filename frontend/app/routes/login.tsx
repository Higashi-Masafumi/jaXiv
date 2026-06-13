import { useEffect } from 'react'
import { useNavigate } from 'react-router'
import { SparklesIcon } from 'lucide-react'
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

  useEffect(() => {
    if (user && !isAnonymous) {
      navigate('/', { replace: true })
    }
  }, [user, isAnonymous, navigate])

  return (
    <main className="relative flex min-h-svh flex-col items-center justify-center overflow-hidden bg-gradient-to-br from-indigo-50/80 via-background to-violet-50/60 px-4 dark:from-indigo-950/20 dark:to-violet-950/20">
      {/* Decorative blobs */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 overflow-hidden"
      >
        <div className="absolute -right-40 -top-40 h-80 w-80 rounded-full bg-indigo-200/30 blur-3xl dark:bg-indigo-500/10" />
        <div className="absolute -left-20 bottom-10 h-64 w-64 rounded-full bg-violet-200/25 blur-3xl dark:bg-violet-500/10" />
      </div>

      <div className="relative flex w-full max-w-sm flex-col items-center gap-8">
        {/* Logo */}
        <div className="flex flex-col items-center gap-3">
          <div className="flex size-12 items-center justify-center rounded-2xl bg-primary shadow-lg shadow-primary/25">
            <SparklesIcon className="size-6 text-primary-foreground" />
          </div>
          <div className="text-center">
            <h1 className="text-2xl font-black tracking-tight text-foreground">
              jaXiv
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              arXiv 論文をブログに変換するAIツール
            </p>
          </div>
        </div>

        {/* Card */}
        <div className="w-full rounded-2xl border border-border/80 bg-white/90 p-7 shadow-xl shadow-indigo-100/40 backdrop-blur-sm dark:bg-card/90 dark:shadow-none">
          <p className="mb-5 text-center text-sm text-muted-foreground">
            PDF論文からもブログを生成できます。
            <br />
            Googleアカウントでログインしてください。
          </p>
          <Button onClick={signInWithGoogle} className="w-full gap-2" size="lg">
            <svg className="size-4" viewBox="0 0 24 24" aria-hidden>
              <path
                fill="currentColor"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="currentColor"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="currentColor"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="currentColor"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            Googleでログイン
          </Button>
        </div>
      </div>
    </main>
  )
}
