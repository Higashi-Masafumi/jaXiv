import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react'
import type { Session, User } from '@supabase/supabase-js'
import { supabase } from '~/lib/supabase'

export type Plan = 'anonymous' | 'free' | 'paid'

interface AuthContextValue {
  user: User | null
  session: Session | null
  /** true if the user has not yet performed a full sign-in (anon or no session) */
  isAnonymous: boolean
  /** Resolved subscription plan. 'anonymous' for unauthenticated guests. */
  plan: Plan
  isPaid: boolean
  refreshPlan: () => Promise<void>
  signInWithGoogle: () => Promise<void>
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [plan, setPlan] = useState<Plan>('anonymous')

  const fetchPlan = useCallback(async (currentSession: Session | null) => {
    if (!currentSession || currentSession.user.is_anonymous) {
      setPlan('anonymous')
      return
    }
    try {
      const apiBase =
        (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? ''
      const res = await fetch(`${apiBase}/api/v1/billing/me`, {
        headers: {
          Authorization: `Bearer ${currentSession.access_token}`,
        },
      })
      if (!res.ok) {
        setPlan('free')
        return
      }
      const body = (await res.json()) as { plan?: string }
      setPlan(body.plan === 'paid' ? 'paid' : 'free')
    } catch {
      setPlan('free')
    }
  }, [])

  useEffect(() => {
    // Restore existing session on mount
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session)
      setUser(data.session?.user ?? null)
      void fetchPlan(data.session)

      // No session at all → sign in anonymously so we always have a JWT
      if (!data.session) {
        supabase.auth.signInAnonymously().then(({ data: anonData }) => {
          setSession(anonData.session)
          setUser(anonData.session?.user ?? null)
          void fetchPlan(anonData.session)
        })
      }
    })

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, newSession) => {
      setSession(newSession)
      setUser(newSession?.user ?? null)
      void fetchPlan(newSession)
    })

    return () => subscription.unsubscribe()
  }, [fetchPlan])

  const refreshPlan = useCallback(async () => {
    await fetchPlan(session)
  }, [fetchPlan, session])

  const signInWithGoogle = useCallback(async () => {
    const redirectTo =
      typeof window !== 'undefined'
        ? `${window.location.origin}/auth/callback`
        : '/auth/callback'
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo },
    })
  }, [])

  const signOut = useCallback(async () => {
    await supabase.auth.signOut()
    // Re-create an anonymous session after sign-out
    const { data } = await supabase.auth.signInAnonymously()
    setSession(data.session)
    setUser(data.session?.user ?? null)
  }, [])

  const isAnonymous = user?.is_anonymous ?? true
  const isPaid = plan === 'paid'

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        isAnonymous,
        plan,
        isPaid,
        refreshPlan,
        signInWithGoogle,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
