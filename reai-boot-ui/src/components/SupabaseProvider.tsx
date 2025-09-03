'use client'

import { createContext, useContext, useEffect, useState } from 'react'
import { User, Session } from '@supabase/supabase-js'
import { supabase, checkUserPermissions, createUserProfile } from '@/lib/supabase'

interface UserPermissions {
  role: 'admin' | 'user' | 'viewer'
  hasAccess: boolean
  isActive: boolean
  canParse: boolean
  canAnalyze: boolean
  canAdmin: boolean
  isNewUser?: boolean
}

interface SupabaseContextType {
  user: User | null
  session: Session | null
  permissions: UserPermissions | null
  loading: boolean
  signOut: () => Promise<void>
  refreshPermissions: () => Promise<void>
}

const SupabaseContext = createContext<SupabaseContextType | undefined>(undefined)

export function SupabaseProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [permissions, setPermissions] = useState<UserPermissions | null>(null)
  const [loading, setLoading] = useState(true)

  const loadUserPermissions = async (userId: string) => {
    try {
      console.log('Loading permissions for user:', userId)
      const userPerms = await checkUserPermissions(userId)
      console.log('User permissions loaded:', userPerms)
      setPermissions(userPerms as UserPermissions)
    } catch (error) {
      console.error('Error loading user permissions:', error)
      // Если профиль не найден, попробуем создать его
      try {
        const { data: { user } } = await supabase.auth.getUser()
        if (user) {
          console.log('Attempting to create profile for user:', user.id)
          const profile = await createUserProfile(user.id, user.email!, user.user_metadata?.full_name)
          console.log('Profile created:', profile)

          // Повторно загружаем разрешения
          const userPerms = await checkUserPermissions(userId)
          setPermissions(userPerms as UserPermissions)
          return
        }
      } catch (createError) {
        console.error('Error creating user profile:', createError)
      }

      setPermissions({
        role: 'viewer',
        hasAccess: false,
        isActive: true,
        canParse: false,
        canAnalyze: false,
        canAdmin: false,
        isNewUser: true
      })
    }
  }

  const refreshPermissions = async () => {
    if (user?.id) {
      await loadUserPermissions(user.id)
    }
  }

  useEffect(() => {
    // Get initial session
    const getInitialSession = async () => {
      const { data: { session }, error } = await supabase.auth.getSession()

      if (error) {
        console.error('Error getting session:', error)
      } else {
        setSession(session)
        setUser(session?.user ?? null)

        // Load permissions if user exists
        if (session?.user) {
          await loadUserPermissions(session.user.id)
        }
      }

      setLoading(false)
    }

    getInitialSession()

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log('Auth state changed:', event, session)
        setSession(session)
        setUser(session?.user ?? null)

        // Load permissions when user changes
        if (session?.user) {
          await loadUserPermissions(session.user.id)
        } else {
          setPermissions(null)
        }

        setLoading(false)
      }
    )

    return () => {
      subscription.unsubscribe()
    }
  }, [])

  const signOut = async () => {
    const { error } = await supabase.auth.signOut()
    if (error) {
      console.error('Error signing out:', error)
    }
  }

  const value = {
    user,
    session,
    permissions,
    loading,
    signOut,
    refreshPermissions,
  }

  return (
    <SupabaseContext.Provider value={value}>
      {children}
    </SupabaseContext.Provider>
  )
}

export function useSupabase() {
  const context = useContext(SupabaseContext)
  if (context === undefined) {
    throw new Error('useSupabase must be used within a SupabaseProvider')
  }
  return context
}
