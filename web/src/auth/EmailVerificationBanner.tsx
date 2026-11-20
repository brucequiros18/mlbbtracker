import { useState } from 'react'
import type { Auth } from 'firebase/auth'

import { firebaseSendEmailVerification } from '../lib/firebase'
import type { Account } from '../lib/types'
import { MailWarningIcon } from '../components/Icons'

/**
 * A quiet prompt to verify the account's email address.
 *
 * Firebase email/password accounts start unverified; the stored flag refreshes
 * the next time the player signs in, so the copy says exactly that instead of
 * pretending the banner will vanish on click.
 */
interface EmailVerificationBannerProps {
  auth: Auth
  account: Account
}

export function EmailVerificationBanner({ auth, account }: EmailVerificationBannerProps) {
  const [pending, setPending] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (account.emailVerified) return null

  const send = async () => {
    setPending(true)
    setError(null)
    try {
      const sentNow = await firebaseSendEmailVerification(auth)
      if (sentNow) {
        setSent(true)
      } else {
        setError('Sign out and sign in again to send a verification link.')
      }
    } catch {
      setError('The link could not be sent. Firebase limits how often it can be resent - try again later.')
    } finally {
      setPending(false)
    }
  }

  return (
    <section
      className="rounded-card border border-warning/40 bg-warning/10 p-4"
      aria-label="Verify your email"
    >
      <div className="flex items-start gap-3">
        <MailWarningIcon size={20} className="mt-0.5 shrink-0 text-warning" />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold">Verify your email</p>
          <p className="mt-0.5 text-sm text-text-2">
            Confirm <span className="break-all text-text-1">{account.email}</span> so the
            account stays recoverable. The check refreshes the next time you sign in.
          </p>
          {sent ? (
            <p className="mt-2 text-sm text-positive" role="status">
              Link sent - check your inbox (and the spam folder).
            </p>
          ) : (
            <>
              {error ? (
                <p className="mt-2 text-sm text-negative" role="alert">
                  {error}
                </p>
              ) : null}
              <button
                type="button"
                onClick={send}
                disabled={pending}
                className="mt-2.5 min-h-11 rounded-control border border-border bg-card px-4 py-2 text-sm font-semibold text-text-1 transition hover:border-text-2 disabled:opacity-50"
              >
                {pending ? 'Sending…' : 'Send verification link'}
              </button>
            </>
          )}
        </div>
      </div>
    </section>
  )
}
