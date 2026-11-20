import { Link } from 'react-router-dom'

import { useAuth } from '../auth/AuthProvider'
import { AccountCard } from '../auth/AccountCard'
import { ProfileSetup } from '../auth/ProfileSetup'
import { LoadingView } from '../components/StateViews'
import { DownloadIcon } from '../components/Icons'

export function AccountPage() {
  const auth = useAuth()

  if (auth.status === 'loading') return <LoadingView message="Checking your session…" />

  if (auth.status === 'signed-out') {
    return (
      <div className="mx-auto max-w-md space-y-5 py-6">
        <header className="text-center">
          <h1 className="font-display text-2xl font-extrabold tracking-tight">Account</h1>
          <p className="text-sm text-text-2">
            Sign in with Google to see your account. Google is the only sign-in method.
          </p>
        </header>
        <Link
          to="/players"
          className="block rounded-control bg-accent py-2.5 text-center text-sm font-semibold text-white transition hover:opacity-90"
        >
          Go to the sign-in page
        </Link>
        <a
          href="/download"
          className="flex items-center justify-center gap-2 rounded-control border border-border py-2.5 text-sm font-semibold text-text-2 transition hover:text-text"
        >
          <DownloadIcon size={16} />
          Download the Android app
        </a>
      </div>
    )
  }

  if (auth.account && !auth.account.profileComplete) return <ProfileSetup />

  return (
    <div className="mx-auto max-w-xl space-y-5">
      <header>
        <h1 className="font-display text-2xl font-extrabold tracking-tight">Account</h1>
        <p className="text-sm text-text-2">Your app account</p>
      </header>
      <AccountCard />
      <a
        href="/download"
        className="flex items-center justify-center gap-2 rounded-control border border-border py-2.5 text-sm font-semibold text-text-2 transition hover:text-text"
      >
        <DownloadIcon size={16} />
        Download the Android app
      </a>
    </div>
  )
}
