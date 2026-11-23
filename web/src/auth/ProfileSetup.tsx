import { useState } from 'react'

import { useAuth, useAuthMutations } from './AuthProvider'
import { Field } from '../pages/PlayersPage'
import { CheckIcon, InfoIcon } from '../components/Icons'

/**
 * Profile setup - the step right after the first sign-in.
 *
 * The player chooses a username, types their MLBB ID and sets an app
 * password. The MLBB ID is **self-declared**: it is stored exactly as
 * typed and is never checked against Moonton.
 *
 * Validation runs on blur using the patterns the server publishes in
 * `GET /api/v1/auth/config`, so the rules shown here are the rules the
 * server enforces.
 */

type FieldErrors = Partial<Record<'username' | 'mlbbId' | 'password' | 'confirm', string>>

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

export function ProfileSetup() {
  const { account, config } = useAuth()
  const { createProfile } = useAuthMutations()

  const [username, setUsername] = useState('')
  const [mlbbId, setMlbbId] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [errors, setErrors] = useState<FieldErrors>({})
  const [error, setError] = useState<string | null>(null)

  const minLength = config?.minPasswordLength ?? 8

  const testPattern = (pattern: string | null | undefined, fallback: RegExp, value: string) => {
    try {
      return pattern ? new RegExp(pattern).test(value) : fallback.test(value)
    } catch {
      return fallback.test(value)
    }
  }

  const validate = (key: keyof FieldErrors): string | null => {
    switch (key) {
      case 'username': {
        const value = username.trim()
        if (!value) return 'Choose a username.'
        if (!testPattern(config?.usernamePattern, /^.{3,24}$/, value)) {
          return 'Use 3-24 letters, numbers, underscores or spaces.'
        }
        return null
      }
      case 'mlbbId': {
        const value = mlbbId.trim()
        if (!value) return 'Enter your MLBB ID.'
        if (!testPattern(config?.mlbbIdPattern, /^\d{4,20}$/, value)) {
          return 'The MLBB ID is 4-20 digits (Profile -> about account).'
        }
        return null
      }
      case 'password': {
        if (!password) return 'Choose an app password.'
        if (password.length < minLength) return `Use at least ${minLength} characters.`
        return null
      }
      case 'confirm':
        return confirm !== password ? 'The two passwords do not match.' : null
    }
  }

  const validateOnBlur = (key: keyof FieldErrors, raw: string) => {
    if (raw === '') return
    const message = validate(key)
    setErrors((current) => ({ ...current, [key]: message ?? undefined }))
  }

  const clearOnType = (key: keyof FieldErrors) => {
    if (!errors[key]) return
    setErrors((current) => ({ ...current, [key]: undefined }))
  }

  const submit = (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)

    const nextErrors: FieldErrors = {}
    for (const key of ['username', 'mlbbId', 'password', 'confirm'] as const) {
      nextErrors[key] = validate(key) ?? undefined
    }
    setErrors(nextErrors)
    if (Object.values(nextErrors).some(Boolean)) return

    createProfile.mutate(
      { username: username.trim(), mlbbId: mlbbId.trim(), password },
      {
        onError: (mutationError) => {
          setError(mutationError instanceof Error ? mutationError.message : 'The profile could not be saved.')
        },
      },
    )
  }

  const passwordMet = password.length >= minLength
  const confirmMet = confirm.length > 0 && confirm === password

  return (
    <div className="mx-auto max-w-md space-y-5 py-6">
      <header>
        <h1 className="font-display text-2xl font-extrabold tracking-tight">Complete your profile</h1>
        <p className="text-sm text-text-2">
          Signed in as {account?.email ?? 'your account'}. Three details are missing.
        </p>
      </header>

      <form
        onSubmit={submit}
        noValidate
        className="space-y-4 rounded-card border border-border bg-card p-5"
      >
        <Field
          label="Username"
          value={username}
          onChange={(value) => {
            setUsername(value)
            clearOnType('username')
          }}
          onBlur={() => validateOnBlur('username', username)}
          placeholder="3-24 letters, numbers, _ or spaces"
          autoComplete="username"
          error={errors.username}
        />
        <Field
          label="MLBB ID"
          value={mlbbId}
          onChange={(value) => {
            setMlbbId(value)
            clearOnType('mlbbId')
          }}
          onBlur={() => validateOnBlur('mlbbId', mlbbId)}
          placeholder="4-20 digits"
          inputMode="numeric"
          error={errors.mlbbId}
          hint="Self-declared - never verified against Moonton."
        />
        <div>
          <Field
            label="App password"
            value={password}
            onChange={(value) => {
              setPassword(value)
              clearOnType('password')
            }}
            onBlur={() => validateOnBlur('password', password)}
            type="password"
            placeholder={`At least ${minLength} characters`}
            autoComplete="new-password"
            error={errors.password}
          />
          <ul className="mt-2 flex flex-wrap gap-x-5 gap-y-1.5 text-xs">
            <Requirement met={passwordMet}>At least {minLength} characters</Requirement>
            <Requirement met={confirmMet}>Both entries match</Requirement>
          </ul>
        </div>
        <Field
          label="Repeat the password"
          value={confirm}
          onChange={(value) => {
            setConfirm(value)
            clearOnType('confirm')
          }}
          onBlur={() => validateOnBlur('confirm', confirm)}
          type="password"
          autoComplete="new-password"
          placeholder="Type it again"
          error={errors.confirm}
        />

        <div className="flex items-start gap-2.5 rounded-control border border-border bg-bg-2 px-3 py-2.5">
          <InfoIcon size={16} className="mt-0.5 shrink-0 text-muted" />
          <p className="text-xs text-text-2">
            Your MLBB ID is self-declared - it is never verified against Moonton. The app
            password is only a confirmation for profile edits; your email login remains
            your sign-in method.
          </p>
        </div>

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
          disabled={createProfile.isPending}
          className="w-full cursor-pointer rounded-control bg-accent py-2.5 text-sm font-semibold text-white transition duration-200 hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:cursor-not-allowed disabled:opacity-50"
        >
          {createProfile.isPending ? 'Saving…' : 'Save profile'}
        </button>
      </form>
    </div>
  )
}
