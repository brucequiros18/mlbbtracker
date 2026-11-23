import { useState } from 'react'
import type { Auth } from 'firebase/auth'

import {
  firebaseSendPasswordReset,
  firebaseSignIn,
  firebaseSignUp,
} from '../lib/firebase'
import { Field } from '../pages/PlayersPage'
import { CheckIcon, MailCheckIcon } from '../components/Icons'

/**
 * Firebase email + password sign-up, sign-in and password reset.
 *
 * This form talks to Firebase directly and receives an ID token. The token is
 * verified **on the Laravel server** (RS256 signature against Firebase's
 * certificates, issuer, audience, expiry) - the browser never decides who the
 * player is.
 *
 * Validation runs on blur (and re-runs while a field with an error is being
 * corrected) instead of only on submit, so mistakes surface while the player
 * is still looking at the field.
 */

type FormMode = 'sign-in' | 'sign-up' | 'reset'
type ResetSent = { email: string }
type FieldErrors = Partial<Record<'email' | 'password' | 'confirm', string>>

interface EmailAuthFormProps {
  auth: Auth
  onIdToken: (idToken: string) => void
  disabled?: boolean
}

/** Firebase's own minimum for email/password accounts. */
const MIN_PASSWORD_LENGTH = 6

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

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
      return `That password is too weak - use at least ${MIN_PASSWORD_LENGTH} characters.`
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

function validateEmail(raw: string): string | null {
  const email = raw.trim()
  if (!email) return 'Enter your email address.'
  if (!EMAIL_PATTERN.test(email)) return 'That email address does not look valid.'
  return null
}

function validatePassword(raw: string, forSignUp: boolean): string | null {
  if (!raw) return 'Enter your password.'
  if (forSignUp && raw.length < MIN_PASSWORD_LENGTH) {
    return `Use at least ${MIN_PASSWORD_LENGTH} characters.`
  }
  return null
}

/** One live requirement line: icon changes with state, not colour alone. */
function Requirement({ met, children }: { met: boolean; children: React.ReactNode }) {
  return (
    <li
      className={`flex items-center gap-1.5 transition-colors duration-200 ${
        met ? 'text-positive' : 'text-muted'
      }`}
    >
      <span
        className={`grid h-4 w-4 shrink-0 place-items-center rounded-full border ${
          met ? 'border-positive bg-positive/15' : 'border-border'
        }`}
        aria-hidden="true"
      >
        {met ? <CheckIcon size={11} strokeWidth={2.6} /> : null}
      </span>
      <span>{children}</span>
      <span className="sr-only">{met ? ' (met)' : ' (not met yet)'}</span>
    </li>
  )
}

export function EmailAuthForm({ auth, onIdToken, disabled }: EmailAuthFormProps) {
  const [mode, setMode] = useState<FormMode>('sign-in')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [errors, setErrors] = useState<FieldErrors>({})
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const [resetSent, setResetSent] = useState<ResetSent | null>(null)

  const switchMode = (next: FormMode) => {
    setMode(next)
    setErrors({})
    setError(null)
    setConfirm('')
    setResetSent(null)
  }

  // Blur validates a non-empty field; typing clears its error as soon as the
  // value becomes valid (no error that cannot be dismissed).
  const validateOnBlur = (key: keyof FieldErrors, raw: string) => {
    if (raw === '') return
    const message =
      key === 'email'
        ? validateEmail(raw)
        : key === 'password'
          ? validatePassword(raw, mode === 'sign-up')
          : raw === password
            ? null
            : 'The two passwords do not match.'
    setErrors((current) => ({ ...current, [key]: message ?? undefined }))
  }

  const clearErrorOnType = (key: keyof FieldErrors) => {
    if (!errors[key]) return
    setErrors((current) => ({ ...current, [key]: undefined }))
  }

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)

    if (mode === 'reset') {
      const emailError = validateEmail(email)
      if (emailError) {
        setErrors({ email: emailError })
        return
      }
      setErrors({})
      setPending(true)
      try {
        await firebaseSendPasswordReset(auth, email)
        // Firebase's enumeration protection succeeds for unknown addresses
        // too, so one reassuring message covers both cases.
        setResetSent({ email: email.trim() })
      } catch (submitError) {
        setError(describeFirebaseError(submitError))
      } finally {
        setPending(false)
      }
      return
    }

    // Validate everything up front so the player sees every problem at once.
    const nextErrors: FieldErrors = {
      email: validateEmail(email) ?? undefined,
      password: validatePassword(password, mode === 'sign-up') ?? undefined,
    }
    if (mode === 'sign-up') {
      nextErrors.confirm =
        password !== confirm ? 'The two passwords do not match.' : undefined
    }
    setErrors(nextErrors)
    if (Object.values(nextErrors).some(Boolean)) return

    setPending(true)
    try {
      const idToken = mode === 'sign-up'
        ? await firebaseSignUp(auth, email, password)
        : await firebaseSignIn(auth, email, password)
      onIdToken(idToken)
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
          className="w-full cursor-pointer rounded-control bg-accent py-2.5 text-sm font-semibold text-white transition duration-200 hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
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

  const passwordMet = password.length >= MIN_PASSWORD_LENGTH
  const confirmMet = confirm.length > 0 && confirm === password

  return (
    <form
      onSubmit={submit}
      noValidate
      className="space-y-4 animate-[fadeIn_0.15s_ease-out]"
    >
      {mode === 'reset' ? (
        <div className="mb-1">
          <p className="font-display text-base font-bold tracking-tight">Reset your password</p>
          <p className="mt-1 text-sm text-text-2">
            Enter your email and we&apos;ll send a reset link.
          </p>
        </div>
      ) : (
        <div
          className="grid grid-cols-2 gap-1 rounded-control border border-border bg-bg-2 p-1"
          role="group"
          aria-label="Sign in or create an account"
        >
          {(['sign-in', 'sign-up'] as const).map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => switchMode(tab)}
              aria-pressed={mode === tab}
              className={`cursor-pointer rounded-[6px] px-3 py-2 text-sm font-semibold transition-colors duration-200 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent ${
                mode === tab
                  ? 'bg-card text-text-1 shadow-sm'
                  : 'text-muted hover:text-text-1'
              }`}
            >
              {tab === 'sign-in' ? 'Sign in' : 'Create account'}
            </button>
          ))}
        </div>
      )}

      <Field
        label="Email"
        value={email}
        onChange={(value) => {
          setEmail(value)
          clearErrorOnType('email')
        }}
        onBlur={() => validateOnBlur('email', email)}
        placeholder="you@example.com"
        type="email"
        autoComplete="email"
        inputMode="email"
        error={errors.email}
      />

      {mode !== 'reset' ? (
        <div>
          <Field
            label="Password"
            value={password}
            onChange={(value) => {
              setPassword(value)
              clearErrorOnType('password')
            }}
            onBlur={() => validateOnBlur('password', password)}
            type="password"
            placeholder={mode === 'sign-up' ? `At least ${MIN_PASSWORD_LENGTH} characters` : 'Your password'}
            autoComplete={mode === 'sign-up' ? 'new-password' : 'current-password'}
            error={errors.password}
          />
          {mode === 'sign-up' ? (
            <ul className="mt-2 flex flex-wrap gap-x-5 gap-y-1.5 text-xs">
              <Requirement met={passwordMet}>
                At least {MIN_PASSWORD_LENGTH} characters
              </Requirement>
              <Requirement met={confirmMet}>Both entries match</Requirement>
            </ul>
          ) : (
            <div className="mt-1.5 flex justify-end">
              <button
                type="button"
                onClick={() => switchMode('reset')}
                className="cursor-pointer text-xs text-muted underline-offset-4 transition-colors duration-200 hover:text-text-1 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
              >
                Forgot password?
              </button>
            </div>
          )}
        </div>
      ) : null}

      {mode === 'sign-up' ? (
        <Field
          label="Repeat the password"
          value={confirm}
          onChange={(value) => {
            setConfirm(value)
            clearErrorOnType('confirm')
          }}
          onBlur={() => validateOnBlur('confirm', confirm)}
          type="password"
          autoComplete="new-password"
          placeholder="Type it again"
          error={errors.confirm}
        />
      ) : null}

      <p className="sr-only" aria-live="polite">
        {error ?? (pending ? pendingLabel : '')}
      </p>

      {error ? (
        <p
          role="alert"
          className="rounded-control border border-negative/40 bg-negative/10 px-3 py-2 text-sm text-negative"
        >
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={pending || disabled}
        className="w-full cursor-pointer rounded-control bg-accent py-2.5 text-sm font-semibold text-white transition duration-200 hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:cursor-not-allowed disabled:opacity-50"
      >
        {pending ? pendingLabel : submitLabel}
      </button>

      {mode === 'reset' ? (
        <button
          type="button"
          onClick={() => switchMode('sign-in')}
          className="w-full cursor-pointer text-center text-sm text-text-2 underline-offset-4 transition-colors duration-200 hover:text-text-1 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
        >
          Back to sign in
        </button>
      ) : (
        <p className="text-center text-xs text-muted">
          {mode === 'sign-up'
            ? 'We send a verification email right after the account is created.'
            : 'New to MLBB Tracker? Pick “Create account” above.'}
        </p>
      )}
    </form>
  )
}
