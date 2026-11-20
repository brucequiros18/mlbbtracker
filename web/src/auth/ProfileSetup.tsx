import { useState } from 'react'

import { useAuth, useAuthMutations } from './AuthProvider'
import { Field } from '../pages/PlayersPage'
import { InfoIcon } from '../components/Icons'

/**
 * Profile setup - the step right after the Google sign-in.
 *
 * The player chooses a username, types their MLBB ID and sets an app
 * password. The MLBB ID is **self-declared**: it is stored exactly as
 * typed and is never checked against Moonton.
 */
export function ProfileSetup() {
  const { account, config } = useAuth()
  const { createProfile } = useAuthMutations()

  const [username, setUsername] = useState('')
  const [mlbbId, setMlbbId] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)

  const minLength = config?.minPasswordLength ?? 8

  const submit = (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)

    if (password !== confirm) {
      setError('The two passwords do not match.')
      return
    }

    createProfile.mutate(
      { username: username.trim(), mlbbId: mlbbId.trim(), password },
      {
        onError: (mutationError) => {
          setError(mutationError instanceof Error ? mutationError.message : 'The profile could not be saved.')
        },
      },
    )
  }

  return (
    <div className="mx-auto max-w-md space-y-5 py-6">
      <header>
        <h1 className="font-display text-2xl font-extrabold tracking-tight">Complete your profile</h1>
        <p className="text-sm text-text-2">
          Signed in as {account?.email ?? 'your account'}. Three details are missing.
        </p>
      </header>

      <form onSubmit={submit} className="space-y-4 rounded-card border border-border bg-card p-5">
        <Field
          label="Username"
          value={username}
          onChange={setUsername}
          placeholder="3-24 letters, numbers, _ or spaces"
          autoComplete="username"
        />
        <Field
          label="MLBB ID"
          value={mlbbId}
          onChange={setMlbbId}
          placeholder="4-20 digits"
          inputMode="numeric"
        />
        <Field
          label="App password"
          value={password}
          onChange={setPassword}
          type="password"
          placeholder={`At least ${minLength} characters`}
          inputMode="text"
          autoComplete="new-password"
        />
        <Field
          label="Repeat the password"
          value={confirm}
          onChange={setConfirm}
          type="password"
          autoComplete="new-password"
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
          <p className="rounded-control border border-negative/40 bg-negative/10 px-3 py-2 text-sm text-negative">
            {error}
          </p>
        ) : null}

        <button
          type="submit"
          disabled={createProfile.isPending}
          className="w-full rounded-control bg-accent py-2.5 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
        >
          {createProfile.isPending ? 'Saving…' : 'Save profile'}
        </button>
      </form>
    </div>
  )
}
