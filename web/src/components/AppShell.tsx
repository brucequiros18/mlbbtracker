import { NavLink, useLocation } from 'react-router-dom'
import { useEffect, useState, type ReactNode } from 'react'

import { useAuth } from '../auth/AuthProvider'
import {
  HeroesIcon,
  HomeIcon,
  MoonIcon,
  PlayersIcon,
  RanksIcon,
  SavedIcon,
  SunIcon,
  TrophyIcon,
  UserIcon,
} from './Icons'
import { theme as themeStore, type Theme } from '../lib/storage'

interface Tab {
  to: string
  label: string
  icon: (props: { size?: number; className?: string }) => ReactNode
}

const TABS: Tab[] = [
  { to: '/', label: 'Home', icon: HomeIcon },
  { to: '/players', label: 'Players', icon: PlayersIcon },
  { to: '/heroes', label: 'Heroes', icon: HeroesIcon },
  { to: '/ranks', label: 'Ranks', icon: RanksIcon },
  { to: '/saved', label: 'Saved', icon: SavedIcon },
]

/**
 * The app shell: a slim header on desktop, a bottom tab bar on phones.
 *
 * The five destinations mirror the Android app: Home, Players, Heroes,
 * Ranks, Saved.
 */
export function AppShell({ children }: { children: ReactNode }) {
  const location = useLocation()
  const { account, status } = useAuth()
  const [mode, setMode] = useState<Theme>(() => themeStore.get())

  useEffect(() => {
    document.documentElement.dataset.theme = mode
  }, [mode])

  const toggleTheme = () => {
    const next: Theme = mode === 'dark' ? 'light' : 'dark'
    setMode(next)
    themeStore.set(next)
  }

  return (
    <div className="flex min-h-screen flex-col bg-bg text-text">
      <header className="sticky top-0 z-30 border-b border-border bg-bg/85 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-6xl items-center gap-3 px-4">
          <NavLink to="/" className="flex items-center gap-2.5" aria-label="MLBB Tracker home">
            <span className="grid h-8 w-8 place-items-center rounded-[10px] bg-accent text-white">
              <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
                <path
                  d="M4 17 9 9l4 5 3-4 4 7"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <circle cx="9" cy="9" r="1.6" fill="currentColor" />
                <circle cx="16" cy="10" r="1.6" fill="currentColor" />
              </svg>
            </span>
            <span className="font-display text-[15px] font-extrabold tracking-tight">
              MLBB Tracker
            </span>
          </NavLink>

          <nav className="ml-4 hidden items-center gap-1 md:flex" aria-label="Primary">
            {TABS.map((tab) => (
              <TabLink key={tab.to} tab={tab} />
            ))}
            <TabLink
              tab={{ to: '/esports', label: 'Esports', icon: TrophyIcon }}
            />
          </nav>

          <div className="ml-auto flex items-center gap-2">
            {status === 'signed-in' && account ? (
              <NavLink
                to="/account"
                className="flex items-center gap-2 rounded-control border border-border bg-card px-2.5 py-1.5 text-sm font-semibold transition hover:border-accent"
              >
                {account.pictureUrl ? (
                  <img
                    src={account.pictureUrl}
                    alt=""
                    className="h-6 w-6 rounded-full bg-elevated object-cover"
                    referrerPolicy="no-referrer"
                  />
                ) : (
                  <UserIcon size={16} className="text-muted" />
                )}
                <span className="hidden sm:inline">{account.username ?? 'Account'}</span>
              </NavLink>
            ) : null}

            <button
              type="button"
              onClick={toggleTheme}
              className="grid h-9 w-9 place-items-center rounded-control border border-border bg-card text-text-2 transition hover:text-text"
              aria-label={mode === 'dark' ? 'Switch to the light theme' : 'Switch to the dark theme'}
              title={mode === 'dark' ? 'Light theme' : 'Dark theme'}
            >
              {mode === 'dark' ? <SunIcon size={17} /> : <MoonIcon size={17} />}
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 pb-28 pt-5 md:pb-12">
        <div key={location.pathname} className="animate-[fadeIn_.18s_ease-out]">
          {children}
        </div>
      </main>

      <nav
        className="safe-bottom fixed inset-x-0 bottom-0 z-30 border-t border-border bg-bg/95 backdrop-blur md:hidden"
        aria-label="Primary"
      >
        <div className="mx-auto grid max-w-lg grid-cols-5">
          {TABS.map((tab) => {
            const Icon = tab.icon
            return (
              <NavLink
                key={tab.to}
                to={tab.to}
                end={tab.to === '/'}
                className={({ isActive }) =>
                  `flex min-h-[56px] flex-col items-center justify-center gap-1 text-[11px] font-semibold transition ${
                    isActive ? 'text-accent' : 'text-muted'
                  }`
                }
              >
                <Icon size={20} />
                {tab.label}
              </NavLink>
            )
          })}
        </div>
      </nav>
    </div>
  )
}

function TabLink({ tab }: { tab: Tab }) {
  const Icon = tab.icon
  return (
    <NavLink
      to={tab.to}
      end={tab.to === '/'}
      className={({ isActive }) =>
        `flex items-center gap-2 rounded-control px-3 py-2 text-sm font-semibold transition ${
          isActive ? 'bg-accent-soft text-accent' : 'text-text-2 hover:text-text'
        }`
      }
    >
      <Icon size={17} />
      {tab.label}
    </NavLink>
  )
}
