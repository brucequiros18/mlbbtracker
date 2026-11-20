import { useState } from 'react'

import { useAuth, useAuthMutations } from './AuthProvider'
import { dateTime } from '../lib/format'
import { LogoutIcon, UserIcon } from '../components/Icons'

/**
 * The signed-in app account.
 *
 * Google is the only credential. The password field here confirms profile
 * edits - it is never a way to sign in.
 */
export function AccountCard() {
  const { account, signOut } = useAuth()
  const { saveProfile } = useAuthMutations()

  const [editing, setEditing] = useState(false)
  const [username, setUsername] = useState(account?.username ?? '')
  const [mlbbId, setMlbbId] = useState(account?.mlbbId ?? '')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  if (!account) return null

  const submit = (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)
    setSaved(false)

    saveProfile.mutate(
      {
        username: username.trim() || undefined,
        mlbbId: mlbbId.trim() || undefined,
        currentPassword,
        newPassword: newPassword ? newPassword : undefined,
      },
      {
        onSuccess: () => {
          setEditing(false)
          setCurrentPassword('')
          setNewPassword('')
          setSaved(true)
        },
        onError: (mutationError) => {
          setError(
            mutationError instanceof Error
              ? mutationError.message
              : 'The profile could not be updated.',
          )
        },
      },
    )
  }

  return (
    <section className="rounded-card border border-border bg-card p-5">
      <div className="flex items-start gap-3">
        {account.pictureUrl ? (
          <img
            src={account.pictureUrl}
            alt=""
            referrerPolicy="no-referrer"
            className="h-12 w-12 rounded-full bg-elevated object-cover"
          />
        ) : (
          <span className="grid h-12 w-12 place-items-center rounded-full bg-elevated text-muted">
            <UserIcon size={22} />
          </span>
        )}
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold">{account.username ?? 'No username yet'}</p>
          <p className="truncate text-xs text-muted">{account.email}</p>
          <p className="mt-1 text-xs text-muted">
            MLBB ID {account.mlbbId ?? '—'}{' '}
            <span className="text-warning">(self-declared, never verified)</span>
          </p>
        </div>
        <button
          type="button"
          onClick={() => signOut()}
          className="inline-flex shrink-0 items-center gap-1.5 rounded-control border border-border px-3 py-1.5 text-xs font-semibold text-text-2 transition hover:border-negative hover:text-negative"
        >
          <LogoutIcon size={14} />
          Sign out
        </button>
      </div>

      <p className="mt-3 text-[11px] text-muted">
        Last sign-in {dateTime(account.lastLoginAt)}
      </p>

      {!editing ? (
        <button
          type="button"
          onClick={() => {
            setEditing(true)
            setSaved(false)
            setError(null)
          }}
          className="mt-3 text-sm font-semibold text-accent transition hover:underline"
        >
          Edit profile
        </button>
      ) : (
        <form onSubmit={submit} className="mt-4 space-y-3 border-t border-border pt-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block">
              <span className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.08em] text-muted">
                Username
              </span>
              <input
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className="w-full rounded-control border border-border bg-bg-2 px-3 py-2 text-sm outline-none transition focus:border-accent"
              />
            </label>
            <label className="block">
              <span className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.08em] text-muted">
                MLBB ID
              </span>
              <input
                value={mlbbId}
                onChange={(event) => setMlbbId(event.target.value)}
                inputMode="numeric"
                className="w-full rounded-control border border-border bg-bg-2 px-3 py-2 text-sm outline-none transition focus:border-accent"
              />
            </label>
          </div>

          <label className="block">
            <span className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.08em] text-muted">
              Current app password
            </span>
            <input
              type="password"
              value={currentPassword}
              onChange={(event) => setCurrentPassword(event.target.value)}
              autoComplete="current-password"
              className="w-full rounded-control border border-border bg-bg-2 px-3 py-2 text-sm outline-none transition focus:border-accent"
            />
          </label>

          <label className="block">
            <span className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.08em] text-muted">
              New app password (optional)
            </span>
            <input
              type="password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
              autoComplete="new-password"
              className="w-full rounded-control border border-border bg-bg-2 px-3 py-2 text-sm outline-none transition focus:border-accent"
            />
          </label>

          {error ? (
            <p className="rounded-control border border-negative/40 bg-negative/10 px-3 py-2 text-sm text-negative">
              {error}
            </p>
          ) : null}
          {saved ? (
            <p className="rounded-control border border-positive/40 bg-positive/10 px-3 py-2 text-sm text-positive">
              The profile was updated.
            </p>
          ) : null}

          <div className="flex gap-2">
            <button
              type="submit"
              disabled={saveProfile.isPending}
              className="rounded-control bg-accent px-5 py-2 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
            >
              {saveProfile.isPending ? 'Saving…' : 'Save changes'}
            </button>
            <button
              type="button"
              onClick={() => {
                setEditing(false)
                setError(null)
                setCurrentPassword('')
                setNewPassword('')
              }}
              className="rounded-control border border-border px-5 py-2 text-sm font-semibold text-text-2 transition hover:text-text"
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </section>
  )
}
