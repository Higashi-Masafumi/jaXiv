import { useEffect } from 'react'
import { useNavigate } from 'react-router'
import { Loader2Icon } from 'lucide-react'
import { supabase } from '~/lib/supabase'

export function meta() {
  return [{ title: '認証中... | jaXiv' }]
}

export default function AuthCallback() {
  const navigate = useNavigate()

  useEffect(() => {
    // Supabase redirects back here with ?code=... after Google OAuth.
    // exchangeCodeForSession() exchanges the code for a session and stores it.
    supabase.auth.exchangeCodeForSession(window.location.href).finally(() => {
      navigate('/', { replace: true })
    })
  }, [navigate])

  return (
    <main className="flex min-h-svh items-center justify-center gap-2 bg-background text-muted-foreground">
      <Loader2Icon className="size-4 animate-spin" aria-hidden />
      <p>認証中...</p>
    </main>
  )
}
