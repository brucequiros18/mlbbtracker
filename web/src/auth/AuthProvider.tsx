import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import { api, ApiError } from '../lib/api'
import { firebaseAuthFromConfig, firebaseSignOut } from '../lib/firebase'
import { accountToken } from '../lib/storage'
import type { Account, AuthConfig } from '../lib/types'

/**
 * App accounts.
 *
 * Sign-in is a **verified ID token**: Firebase (email + password) or Google.
 * The session token here comes from the Laravel server after it verified the
 * ID token locally. The username, MLBB ID and app password are profile data -
 * the MLBB ID is self-declared and never verified.
 */
interface AuthContextValue {
  account: Account | null
  token: string | null
  status: 'loading' | 'signed-out' | 'signed-in'
  config: AuthConfig | null
  configError: ApiError | null
  signInWithFirebase: (idToken: string) => Promise<Account>
  signInWithGoogle: (credential: string) => Promise<Account>
  register: (profile: { username: string; mlbbId: string; password: string }) => Promise<Account>
  updateProfile: (profile: {
    username?: string
    mlbbId?: string
    currentPassword: string
    newPassword?: string
  }) => Promise<Account>
  signOut: () => Promise<void>
  refresh: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [token, setToken] = useState<string | null>(() => accountToken.get())
  const [account, setAccount] = useState<Account | null>(null)
  const [status, setStatus] = useState<AuthContextValue['status']>('loading')

  const configQuery = useQuery({
    queryKey: ['auth', 'config'],
    queryFn: ({ signal }) => api.auth.config(signal),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  })

  const accountQuery = useQuery({
    queryKey: ['auth', 'me', token],
    queryFn: ({ signal }) => api.auth.me(token as string, signal),
    enabled: token !== null,
    staleTime: 60 * 1000,
    retry: false,
  })

  useEffect(() => {
    if (!token) {
      setAccount(null)
      setStatus('signed-out')
      return
    }

    if (accountQuery.isPending) {
      setStatus('loading')
      return
    }

    if (accountQuery.data) {
      setAccount(accountQuery.data)
      setStatus('signed-in')
      return
    }

    if (accountQuery.error instanceof ApiError && accountQuery.error.status === 401) {
      // The session expired or was revoked: forget it locally.
      accountToken.set(null)
      setToken(null)
      setAccount(null)
      setStatus('signed-out')
      return
    }

    if (accountQuery.error) {
      // A network problem is not a reason to sign the player out.
      setStatus('signed-out')
    }
  }, [token, accountQuery.isPending, accountQuery.data, accountQuery.error])

  const exchangeSession = useCallback(async (
    method: 'firebase' | 'google',
    idToken: string,
  ): Promise<Account> => {
    const result = method === 'firebase'
      ? await api.auth.signInWithFirebase(idToken)
      : await api.auth.signInWithGoogle(idToken)
    accountToken.set(result.sessionToken)
    setToken(result.sessionToken)
    setAccount(result.user)
    setStatus('signed-in')
    await queryClient.invalidateQueries({ queryKey: ['auth'] })
    return result.user
  }, [queryClient])

  const signInWithFirebase = useCallback(
    (idToken: string) => exchangeSession('firebase', idToken),
    [exchangeSession],
  )

  const signInWithGoogle = useCallback(
    (credential: string) => exchangeSession('google', credential),
    [exchangeSession],
  )

  const register = useCallback(
    async (profile: { username: string; mlbbId: string; password: string }) => {
      if (!token) throw new ApiError('Sign in with Google first.', 'AUTH_REQUIRED', 401)
      const updated = await api.auth.register(token, profile)
      setAccount(updated)
      await queryClient.invalidateQueries({ queryKey: ['auth'] })
      return updated
    },
    [token, queryClient],
  )

  const updateProfile = useCallback(
    async (profile: {
      username?: string
      mlbbId?: string
      currentPassword: string
      newPassword?: string
    }) => {
      if (!token) throw new ApiError('Sign in with Google first.', 'AUTH_REQUIRED', 401)
      const updated = await api.auth.updateProfile(token, profile)
      setAccount(updated)
      await queryClient.invalidateQueries({ queryKey: ['auth'] })
      return updated
    },
    [token, queryClient],
  )

  const signOut = useCallback(async () => {
    const current = token
    accountToken.set(null)
    setToken(null)
    setAccount(null)
    setStatus('signed-out')
    queryClient.clear()
    if (current) {
      try {
        await api.auth.logout(current)
      } catch {
        // The local session is already gone; a failed server call is fine.
      }
    }
    // Also forget the underlying Firebase session, if one exists.
    if (configQuery.data) {
      const firebaseAuth = firebaseAuthFromConfig(configQuery.data)
      if (firebaseAuth) {
        try {
          await firebaseSignOut(firebaseAuth)
        } catch {
          // Already signed out of Firebase; nothing to recover.
        }
      }
    }
  }, [token, queryClient, configQuery.data])

  const refresh = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: ['auth'] })
  }, [queryClient])

  const value = useMemo<AuthContextValue>(
    () => ({
      account,
      token,
      status,
      config: configQuery.data ?? null,
      configError: configQuery.error instanceof ApiError ? configQuery.error : null,
      signInWithFirebase,
      signInWithGoogle,
      register,
      updateProfile,
      signOut,
      refresh,
    }),
    [
      account,
      token,
      status,
      configQuery.data,
      configQuery.error,
      signInWithFirebase,
      signInWithGoogle,
      register,
      updateProfile,
      signOut,
      refresh,
    ],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside <AuthProvider>.')
  return context
}

/** Convenience hook for the mutations that need an error surface. */
export function useAuthMutations() {
  const auth = useAuth()
  const queryClient = useQueryClient()

  const signIn = useMutation({
    mutationFn: (idToken: string) => auth.signInWithFirebase(idToken),
  })

  const createProfile = useMutation({
    mutationFn: (profile: { username: string; mlbbId: string; password: string }) =>
      auth.register(profile),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['auth'] }),
  })

  const saveProfile = useMutation({
    mutationFn: (profile: {
      username?: string
      mlbbId?: string
      currentPassword: string
      newPassword?: string
    }) => auth.updateProfile(profile),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['auth'] }),
  })

  return { signIn, createProfile, saveProfile }
}
