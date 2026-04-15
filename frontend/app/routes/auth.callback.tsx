import { useEffect } from 'react'
import { useNavigate } from 'react-router'
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
    <main className="flex min-h-svh items-center justify-center bg-hero-background text-hero-foreground">
      <p className="text-hero-muted">認証中...</p>
    </main>
  )
}
