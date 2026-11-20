import { useState } from 'react'
import type { Auth } from 'firebase/auth'

import {
  firebaseSendPasswordReset,
  firebaseSignIn,
  firebaseSignUp,
} from '../lib/firebase'
import { Field } from '../pages/PlayersPage'
import { MailCheckIcon } from '../components/Icons'

/**
 * Firebase email + password sign-up, sign-in and password reset.
 *
 * This form talks to Firebase directly and receives an ID token. The token is
 * verified **on the Laravel server** (RS256 signature against Firebase's
 * certificates, issuer, audience, expiry) - the browser never decides who the
 * player is.
 */

type FormMode = 'sign-in' | 'sign-up' | 'reset'
type ResetSent = { email: string }

interface EmailAuthFormProps {
  auth: Auth
  onIdToken: (idToken: string) => void
  disabled?: boolean
}

/** Map raw Firebase SDK errors to short, honest messages. */
function describeFirebaseError(error: unknown): string {
  const code = typeof error === 'object' && error !== null && 'code' in error
    ? String((error as { code: unknown }).code)
    : ''

  switch (code) {
    case 'auth/invalid-email':
      return 'That email address does not look valid.'
    case 'auth/missing-password':
      return 'Enter a password.'
    case 'auth/weak-password':
      return 'That password is too weak - use at least 6 characters.'
    case 'auth/email-already-in-use':
      return 'An account with that email already exists. Sign in instead.'
    case 'auth/invalid-credential':
    case 'auth/wrong-password':
    case 'auth/user-not-found':
      return 'That email and password do not match an account.'
    case 'auth/too-many-requests':
      return 'Too many attempts. Wait a moment and try again.'
    case 'auth/network-request-failed':
      return 'Could not reach Firebase. Check your connection and try again.'
    case 'auth/operation-not-allowed':
      return 'Email/password sign-in is not enabled for this Firebase project.'
    default:
      return 'Sign-in failed. Please try again.'
  }
}

export function EmailAuthForm({ auth, onIdToken, disabled }: EmailAuthFormProps) {
  const [mode, setMode] = useState<FormMode>('sign-in')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const [resetSent, setResetSent] = useState<ResetSent | null>(null)

  const switchMode = (next: FormMode) => {
    setMode(next)
    setError(null)
    setConfirm('')
    setResetSent(null)
  }

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)

    if (mode === 'sign-up' && password !== confirm) {
      setError('The two passwords do not match.')
      return
    }

    setPending(true)
    try {
      if (mode === 'reset') {
        await firebaseSendPasswordReset(auth, email)
        // Firebase's enumeration protection succeeds for unknown addresses
        // too, so one reassuring message covers both cases.
        setResetSent({ email: email.trim() })
      } else {
        const idToken = mode === 'sign-up'
          ? await firebaseSignUp(auth, email, password)
          : await firebaseSignIn(auth, email, password)
        onIdToken(idToken)
      }
    } catch (submitError) {
      setError(describeFirebaseError(submitError))
    } finally {
      setPending(false)
    }
  }

  if (resetSent) {
    return (
      <div
        className="space-y-4 text-center"
        role="status"
        aria-live="polite"
      >
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-accent-soft text-accent">
          <MailCheckIcon size={24} />
        </div>
        <div>
          <p className="font-display text-base font-bold tracking-tight">Check your inbox</p>
          <p className="mt-1.5 text-sm text-text-2">
            If an account exists for <span className="font-medium text-text-1">{resetSent.email}</span>,
            a reset link is on its way. It expires in about an hour.
          </p>
        </div>
        <button
          type="button"
          onClick={() => switchMode('sign-in')}
          className="w-full rounded-control bg-accent py-2.5 text-sm font-semibold text-white transition hover:opacity-90"
        >
          Back to sign in
        </button>
      </div>
    )
  }

  const submitLabel = mode === 'sign-up'
    ? 'Create account'
    : mode === 'reset'
      ? 'Send reset link'
      : 'Sign in'
  const pendingLabel = mode === 'sign-up'
    ? 'Creating your account…'
    : mode === 'reset'
      ? 'Sending the link…'
      : 'Signing in…'

  return (
    <form onSubmit={submit} className="space-y-4 animate-[fadeIn_0.15s_ease-out]">
      <Field
        label="Email"
        value={email}
        onChange={setEmail}
        placeholder="you@example.com"
        type="email"
        autoComplete="email"
      />
      {mode !== 'reset' ? (
        <div>
          <Field
            label="Password"
            value={password}
            onChange={setPassword}
            type="password"
            placeholder={mode === 'sign-up' ? 'At least 6 characters' : 'Your password'}
            autoComplete={mode === 'sign-up' ? 'new-password' : 'current-password'}
          />
          {mode === 'sign-in' ? (
            <div className="mt-1.5 flex justify-end">
              <button
                type="button"
                onClick={() => switchMode('reset')}
                className="text-xs text-muted underline-offset-4 transition hover:text-text-1 hover:underline"
              >
                Forgot password?
              </button>
            </div>
          ) : null}
        </div>
      ) : null}
      {mode === 'sign-up' ? (
        <Field
          label="Repeat the password"
          value={confirm}
          onChange={setConfirm}
          type="password"
          autoComplete="new-password"
        />
      ) : null}

      <p className="sr-only" aria-live="polite">
        {error ?? (pending ? pendingLabel : '')}
      </p>

      {error ? (
        <p className="rounded-control border border-negative/40 bg-negative/10 px-3 py-2 text-sm text-negative">
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={pending || disabled}
        className="w-full rounded-control bg-accent py-2.5 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
      >
        {pending ? pendingLabel : submitLabel}
      </button>

      {mode === 'reset' ? (
        <button
          type="button"
          onClick={() => switchMode('sign-in')}
          className="w-full text-center text-sm text-text-2 underline-offset-4 transition hover:text-text-1 hover:underline"
        >
          Back to sign in
        </button>
      ) : (
        <button
          type="button"
          onClick={() => switchMode(mode === 'sign-up' ? 'sign-in' : 'sign-up')}
          className="w-full text-center text-sm text-text-2 underline-offset-4 transition hover:text-text-1 hover:underline"
        >
          {mode === 'sign-up'
            ? 'Already have an account? Sign in'
            : 'New here? Create an account'}
        </button>
      )}
    </form>
  )
}
