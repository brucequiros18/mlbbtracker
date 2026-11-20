import { useMutation, useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { api, ApiError } from '../lib/api'
import { useAuth, useAuthMutations } from '../auth/AuthProvider'
import { usePlayer } from '../players/PlayerProvider'
import { EmailAuthForm } from '../auth/EmailAuthForm'
import { GoogleButton } from '../auth/GoogleButton'
import { ProfileSetup } from '../auth/ProfileSetup'
import { AccountCard } from '../auth/AccountCard'
import { firebaseAuthFromConfig } from '../lib/firebase'
import { count, percent } from '../lib/format'
import { EmptyView, ErrorView, LoadingView } from '../components/StateViews'
import { StatTile } from '../components/StatTile'
import { HeroAvatar } from '../components/HeroAvatar'
import { InfoIcon, LogoutIcon } from '../components/Icons'

export function PlayersPage() {
  const auth = useAuth()
  const player = usePlayer()

  if (auth.status === 'loading') return <LoadingView message="Checking your session…" />

  if (auth.status === 'signed-out') return <SignInPanel />

  if (auth.account && !auth.account.profileComplete) return <ProfileSetup />

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-display text-2xl font-extrabold tracking-tight">Players</h1>
        <p className="text-sm text-text-2">Your account and your own tracked statistics</p>
      </header>

      {auth.account ? <AccountCard /> : null}

      {player.status === 'connected' ? <PlayerDashboard /> : <ConnectPanel />}
    </div>
  )
}

function SignInPanel() {
  const { config, configError } = useAuth()
  const { signIn } = useAuthMutations()
  const [error, setError] = useState<string | null>(null)

  const handleIdToken = (idToken: string) => {
    setError(null)
    signIn.mutate(idToken, {
      onError: (mutationError) => {
        setError(
          mutationError instanceof Error
            ? mutationError.message
            : 'Sign-in could not be completed.',
        )
      },
    })
  }

  const firebaseReady = Boolean(
    config?.firebaseEnabled && config.firebaseApiKey && config.firebaseProjectId,
  )
  const googleReady = Boolean(config?.googleSignInEnabled && config.googleClientId)
  const anyMethod = firebaseReady || googleReady

  return (
    <div className="mx-auto max-w-md space-y-5 py-6">
      <header className="text-center">
        <h1 className="font-display text-2xl font-extrabold tracking-tight">Sign in</h1>
        <p className="text-sm text-text-2">
          Sign in or create an account with your email.
        </p>
      </header>

      <div className="rounded-card border border-border bg-card p-5">
        {configError ? (
          <p className="text-sm text-negative">
            The server could not be reached, so sign-in is unavailable right now.
          </p>
        ) : !config ? (
          <LoadingView message="Checking the sign-in configuration…" />
        ) : !anyMethod ? (
          <div className="flex items-start gap-3">
            <InfoIcon size={20} className="mt-0.5 shrink-0 text-warning" />
            <div>
              <p className="text-sm font-semibold">Sign-in is not configured yet</p>
              <p className="mt-1 text-sm text-text-2">
                This server has no Firebase project or OAuth client ID, so no
                sign-in method can work. The maintainer sets{' '}
                <code className="text-xs">MLBB_FIREBASE_PROJECT_ID</code> (or{' '}
                <code className="text-xs">MLBB_GOOGLE_CLIENT_ID</code>) to enable
                one.
              </p>
            </div>
          </div>
        ) : (
          <>
            {firebaseReady && config.firebaseApiKey && config.firebaseProjectId ? (
              <EmailAuthForm
                auth={firebaseAuthFromConfig(config)!}
                onIdToken={handleIdToken}
                disabled={signIn.isPending}
              />
            ) : null}

            {firebaseReady && googleReady ? (
              <div className="my-4 flex items-center gap-3" aria-hidden>
                <span className="h-px flex-1 bg-border" />
                <span className="text-xs text-muted">or</span>
                <span className="h-px flex-1 bg-border" />
              </div>
            ) : null}

            {googleReady && config.googleClientId ? (
              <>
                <GoogleButton
                  clientId={config.googleClientId}
                  onCredential={handleIdToken}
                  disabled={signIn.isPending}
                />
                <p className="mt-2 text-center text-xs text-muted">
                  Google sign-in is also available.
                </p>
              </>
            ) : null}

            {signIn.isPending ? (
              <p className="mt-3 text-center text-sm text-muted">Signing in…</p>
            ) : null}
            {error ? (
              <p className="mt-3 rounded-control border border-negative/40 bg-negative/10 px-3 py-2 text-sm text-negative">
                {error}
              </p>
            ) : null}
          </>
        )}
      </div>

      <p className="text-xs text-muted">
        Your email is the sign-in credential. The app password you choose later never
        signs you in — it only confirms changes to your profile.
      </p>
    </div>
  )
}

function ConnectPanel() {
  const { connect } = usePlayer()
  const [playerId, setPlayerId] = useState('')
  const [zoneId, setZoneId] = useState('')
  const [code, setCode] = useState('')
  const [stage, setStage] = useState<'idle' | 'code-sent'>('idle')
  const [error, setError] = useState<string | null>(null)

  const start = useMutation({
    mutationFn: () => api.players.startConnect(playerId.trim(), zoneId.trim()),
    onSuccess: () => {
      setStage('code-sent')
      setError(null)
    },
    onError: (mutationError) => {
      setError(mutationError instanceof Error ? mutationError.message : 'The code could not be sent.')
    },
  })

  const verify = useMutation({
    mutationFn: () => connect(playerId.trim(), zoneId.trim(), code.trim()),
    onError: (mutationError) => {
      setError(
        mutationError instanceof Error
          ? mutationError.message
          : 'The verification code was not accepted.',
      )
    },
  })

  const idPattern = /^\d+$/

  return (
    <section className="rounded-card border border-border bg-card p-5">
      <h2 className="font-display text-lg font-bold">Connect your MLBB account</h2>
      <p className="mt-1 text-sm text-text-2">
        Enter your own Player ID and Zone ID. A one-time code arrives in your in-game mailbox —
        no password is ever requested or stored.
      </p>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <Field
          label="Player ID"
          value={playerId}
          onChange={setPlayerId}
          placeholder="123456789"
          inputMode="numeric"
          disabled={stage === 'code-sent'}
        />
        <Field
          label="Zone ID"
          value={zoneId}
          onChange={setZoneId}
          placeholder="2222"
          inputMode="numeric"
          disabled={stage === 'code-sent'}
        />
      </div>

      {stage === 'idle' ? (
        <button
          type="button"
          onClick={() => start.mutate()}
          disabled={start.isPending || !idPattern.test(playerId.trim()) || !idPattern.test(zoneId.trim())}
          className="mt-4 w-full rounded-control bg-accent py-2.5 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40 sm:w-auto sm:px-6"
        >
          {start.isPending ? 'Sending the code…' : 'Send the verification code'}
        </button>
      ) : (
        <div className="mt-4 space-y-3">
          <p className="rounded-control border border-positive/40 bg-positive/10 px-3 py-2 text-sm text-text-2">
            A verification code was sent to your in-game mailbox. It expires in a few minutes.
          </p>
          <Field
            label="Verification code"
            value={code}
            onChange={setCode}
            placeholder="123456"
            inputMode="numeric"
          />
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => verify.mutate()}
              disabled={verify.isPending || !/^\d{4,8}$/.test(code.trim())}
              className="rounded-control bg-accent px-5 py-2.5 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {verify.isPending ? 'Verifying…' : 'Connect'}
            </button>
            <button
              type="button"
              onClick={() => {
                setStage('idle')
                setCode('')
                setError(null)
              }}
              className="rounded-control border border-border px-5 py-2.5 text-sm font-semibold text-text-2 transition hover:text-text"
            >
              Start over
            </button>
          </div>
        </div>
      )}

      {error ? (
        <p className="mt-3 rounded-control border border-negative/40 bg-negative/10 px-3 py-2 text-sm text-negative">
          {error}
        </p>
      ) : null}
    </section>
  )
}

function PlayerDashboard() {
  const { token, profile, disconnect } = usePlayer()

  const stats = useQuery({
    queryKey: ['player', 'stats', token],
    queryFn: ({ signal }) => api.players.stats(token as string, signal),
    enabled: token !== null,
    staleTime: 60 * 1000,
  })

  const matches = useQuery({
    queryKey: ['player', 'matches', token],
    queryFn: ({ signal }) => api.players.matches(token as string, 10, null, signal),
    enabled: token !== null,
    staleTime: 60 * 1000,
  })

  const frequent = useQuery({
    queryKey: ['player', 'heroes', token],
    queryFn: ({ signal }) => api.players.frequentHeroes(token as string, 5, signal),
    enabled: token !== null,
    staleTime: 60 * 1000,
  })

  const statData = stats.data

  return (
    <section className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <HeroAvatar name={profile?.ign ?? 'Player'} src={profile?.avatar} size={48} />
          <div>
            <h2 className="font-display text-lg font-bold">{profile?.ign ?? 'Your account'}</h2>
            <p className="text-xs text-muted">
              Player ID {profile?.playerId ?? '—'} · Zone {profile?.zoneId ?? '—'}
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => disconnect()}
          className="inline-flex items-center gap-2 rounded-control border border-border px-4 py-2 text-sm font-semibold text-text-2 transition hover:border-negative hover:text-negative"
        >
          <LogoutIcon size={16} />
          Disconnect
        </button>
      </div>

      {stats.isPending ? (
        <LoadingView message="Loading your statistics…" />
      ) : stats.isError ? (
        <ErrorView
          message={
            stats.error instanceof Error
              ? stats.error.message
              : 'Your statistics could not be loaded.'
          }
          onRetry={() => stats.refetch()}
        />
      ) : statData ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatTile label="Matches" value={count(statData.totalMatches)} />
          <StatTile label="Wins" value={count(statData.wins)} />
          <StatTile label="Win rate" value={percent(statData.winRate)} tone="positive" />
          <StatTile label="MVP" value={count(statData.mvpCount)} />
          <StatTile label="Avg score" value={statData.avgScore ?? '—'} />
          <StatTile label="Playtime" value={statData.playtimeHours !== null ? `${statData.playtimeHours.toFixed(1)} h` : '—'} />
          <StatTile label="Win streak" value={count(statData.winStreak)} />
          <StatTile label="Level" value={count(profile?.level ?? null)} />
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <div>
          <h3 className="mb-2 font-display text-base font-bold">Frequent heroes</h3>
          {frequent.isPending ? (
            <LoadingView message="Loading…" />
          ) : frequent.isError ? (
            <ErrorView
              message={
                frequent.error instanceof Error
                  ? frequent.error.message
                  : 'Your hero list could not be loaded.'
              }
              onRetry={() => frequent.refetch()}
            />
          ) : (frequent.data ?? []).length === 0 ? (
            <EmptyView
              title="No hero data yet"
              message="The provider has not reported any hero usage for this account."
            />
          ) : (
            <ul className="space-y-2">
              {(frequent.data ?? []).map((hero, index) => (
                <li
                  key={`${hero.heroId ?? 'hero'}-${index}`}
                  className="flex items-center gap-3 rounded-card border border-border bg-card p-3"
                >
                  <HeroAvatar name={hero.heroName ?? '?'} src={hero.heroIcon} size={32} />
                  <span className="flex-1 truncate text-sm font-semibold">
                    {hero.heroName ?? 'Unknown hero'}
                  </span>
                  <span className="stat text-xs text-muted">{count(hero.totalMatches)} games</span>
                  <span className="stat text-sm font-bold text-positive">
                    {percent(hero.winRate)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <h3 className="mb-2 font-display text-base font-bold">Recent matches</h3>
          {matches.isPending ? (
            <LoadingView message="Loading…" />
          ) : matches.isError ? (
            <ErrorView
              message={
                matches.error instanceof Error
                  ? matches.error.message
                  : 'Your match history could not be loaded.'
              }
              onRetry={() => matches.refetch()}
            />
          ) : (matches.data?.data ?? []).length === 0 ? (
            <EmptyView
              title="No matches yet"
              message="The provider has not reported any matches for this account."
            />
          ) : (
            <ul className="space-y-2">
              {(matches.data?.data ?? []).map((match, index) => (
                <li
                  key={match.battleId ?? `match-${index}`}
                  className="flex items-center gap-3 rounded-card border border-border bg-card p-3"
                >
                  <span
                    className={`grid h-8 w-8 shrink-0 place-items-center rounded-full text-xs font-bold ${
                      match.won ? 'bg-positive/15 text-positive' : 'bg-negative/15 text-negative'
                    }`}
                    title={match.won ? 'Victory' : 'Defeat'}
                  >
                    {match.won ? 'W' : 'L'}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-semibold">
                      {match.heroName ?? 'Unknown hero'}
                    </span>
                    <span className="stat block text-xs text-muted">
                      {match.kills} / {match.deaths} / {match.assists} · KDA {match.kda.toFixed(2)}
                      {match.mvp ? ' · MVP' : ''}
                    </span>
                  </span>
                  <span className="stat shrink-0 text-xs text-muted">
                    {match.playedAt ? new Date(match.playedAt).toLocaleDateString('en-GB') : '—'}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  )
}

export function Field({
  label,
  value,
  onChange,
  placeholder,
  type = 'text',
  inputMode,
  disabled,
  autoComplete,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  type?: string
  inputMode?: 'text' | 'numeric' | 'email'
  disabled?: boolean
  autoComplete?: string
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.08em] text-muted">
        {label}
      </span>
      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        inputMode={inputMode}
        disabled={disabled}
        autoComplete={autoComplete}
        className="w-full rounded-control border border-border bg-bg-2 px-3 py-2.5 text-sm outline-none transition focus:border-accent disabled:opacity-60"
      />
    </label>
  )
}

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return 'Something went wrong.'
}
