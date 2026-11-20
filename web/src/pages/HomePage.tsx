import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { api } from '../lib/api'
import { percent } from '../lib/format'
import { HeroAvatar } from '../components/HeroAvatar'
import { ErrorView, LoadingView } from '../components/StateViews'
import { SectionHeader } from '../components/StatTile'
import {
  ChevronRightIcon,
  DownloadIcon,
  HeroesIcon,
  InfoIcon,
  RanksIcon,
  SearchIcon,
  TrophyIcon,
} from '../components/Icons'

export function HomePage() {
  const rankings = useQuery({
    queryKey: ['heroes', 'rankings', { days: '7', rank: 'all', sort: 'win_rate' }],
    queryFn: ({ signal }) =>
      api.heroes.rankings({ days: '7', rank: 'all', sort: 'win_rate' }, signal),
    staleTime: 5 * 60 * 1000,
  })

  const trending = rankings.data?.slice(0, 5) ?? []

  return (
    <div className="space-y-7">
      <header>
        <h1 className="font-display text-2xl font-extrabold tracking-tight">MLBB Tracker</h1>
        <p className="text-sm text-text-2">
          Competitive hero analytics for Mobile Legends: Bang Bang
        </p>
      </header>

      <Link
        to="/players"
        className="flex items-center gap-3 rounded-card border border-border bg-card p-4 transition hover:border-accent"
      >
        <SearchIcon size={20} className="text-accent" />
        <span className="flex-1">
          <span className="block text-sm font-semibold">Connect your account</span>
          <span className="block text-xs text-muted">Your stats, KDA & match history</span>
        </span>
        <ChevronRightIcon size={18} className="text-muted" />
      </Link>

      <div className="flex items-start gap-3 rounded-card border border-warning/40 bg-warning/10 p-4">
        <InfoIcon size={20} className="mt-0.5 shrink-0 text-warning" />
        <p className="text-sm text-text-2">
          Connect your own account with the one-time code from your in-game mailbox to see
          your real stats, KDA and match history. Looking up other players is not possible —
          no public source exposes it.
        </p>
      </div>

      <section>
        <SectionHeader
          title="Trending Heroes"
          subtitle="Highest win rate · last 7 days · all ranks"
        />
        {rankings.isPending ? (
          <LoadingView message="Fetching live rankings…" />
        ) : rankings.isError ? (
          <ErrorView
            message={
              rankings.error instanceof Error
                ? rankings.error.message
                : 'The rankings could not be loaded.'
            }
            onRetry={() => rankings.refetch()}
          />
        ) : trending.length === 0 ? (
          <p className="rounded-card border border-border bg-card px-4 py-8 text-center text-sm text-muted">
            The provider returned no hero statistics.
          </p>
        ) : (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            {trending.map((hero) => (
              <Link
                key={hero.id || hero.slug}
                to={`/heroes/${hero.slug}`}
                className="rounded-card border border-border bg-card p-3 transition hover:border-accent"
              >
                <HeroAvatar name={hero.name} src={hero.headImage} size={44} />
                <p className="mt-3 truncate text-sm font-semibold">{hero.name}</p>
                {hero.tier ? (
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">
                    Tier {hero.tier}
                  </p>
                ) : null}
                <p className="stat mt-2 font-display text-lg font-bold text-positive">
                  {percent(hero.winRate)}
                </p>
                <p className="text-[11px] uppercase tracking-[0.08em] text-muted">Win rate</p>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section>
        <SectionHeader title="Explore" />
        <div className="grid gap-3 sm:grid-cols-2">
          <ExploreTile
            to="/heroes"
            icon={<HeroesIcon size={22} className="text-accent" />}
            title="Heroes"
            subtitle="Roster, roles and builds"
          />
          <ExploreTile
            to="/ranks"
            icon={<RanksIcon size={22} className="text-accent" />}
            title="Ranks"
            subtitle="Meta rankings and trends"
          />
          <ExploreTile
            to="/esports"
            icon={<TrophyIcon size={22} className="text-accent" />}
            title="Esports"
            subtitle="MPL ID · PH · MY · KH standings"
          />
          <ExploreTile
            to="/download"
            icon={<DownloadIcon size={22} className="text-accent" />}
            title="Get the Android app"
            subtitle="Download the APK from the release page"
            external
          />
        </div>
      </section>

      <p className="rounded-card border border-border bg-bg-2 px-4 py-3 text-xs text-muted">
        Hero stats are live from the Rone Arena community API and MLBBDex, served through the
        MLBB Tracker backend. Unofficial fan project — not affiliated with Moonton.
      </p>
    </div>
  )
}

function ExploreTile({
  to,
  icon,
  title,
  subtitle,
  external = false,
}: {
  to: string
  icon: React.ReactNode
  title: string
  subtitle: string
  external?: boolean
}) {
  const content = (
    <>
      {icon}
      <p className="mt-3 text-sm font-semibold">{title}</p>
      <p className="text-xs text-muted">{subtitle}</p>
    </>
  )

  if (external) {
    return (
      <a
        href={to}
        className="rounded-card border border-border bg-card p-4 transition hover:border-accent"
      >
        {content}
      </a>
    )
  }

  return (
    <Link
      to={to}
      className="rounded-card border border-border bg-card p-4 transition hover:border-accent"
    >
      {content}
    </Link>
  )
}
