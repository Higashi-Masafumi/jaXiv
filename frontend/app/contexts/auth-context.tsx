import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react'
import type { Session, User } from '@supabase/supabase-js'
import { supabase } from '~/lib/supabase'

interface AuthContextValue {
  user: User | null
  session: Session | null
  /** true if the user has not yet performed a full sign-in (anon or no session) */
  isAnonymous: boolean
  signInWithGoogle: () => Promise<void>
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)

  useEffect(() => {
    // Restore existing session on mount
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session)
      setUser(data.session?.user ?? null)

      // No session at all → sign in anonymously so we always have a JWT
      if (!data.session) {
        supabase.auth.signInAnonymously().then(({ data: anonData }) => {
          setSession(anonData.session)
          setUser(anonData.session?.user ?? null)
        })
      }
    })

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, newSession) => {
      setSession(newSession)
      setUser(newSession?.user ?? null)
    })

    return () => subscription.unsubscribe()
  }, [])

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

  return (
    <AuthContext.Provider
      value={{ user, session, isAnonymous, signInWithGoogle, signOut }}
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
