import { useQuery } from '@tanstack/react-query'
import { Suspense, lazy } from 'react'
import { Link, useParams } from 'react-router-dom'

import { api } from '../lib/api'
import { percent } from '../lib/format'
import { HeroAvatar } from '../components/HeroAvatar'
import { ErrorView, LoadingView } from '../components/StateViews'
import { StatTile } from '../components/StatTile'
import { ChevronLeftIcon, TrendDownIcon, TrendUpIcon } from '../components/Icons'

// The charting library is only needed on this page, so it is loaded on
// demand instead of weighing down every first paint.
const HistoryChart = lazy(() =>
  import('../components/Charts').then((module) => ({ default: module.HistoryChart })),
)
const TrendChart = lazy(() =>
  import('../components/Charts').then((module) => ({ default: module.TrendChart })),
)

export function HeroDetailPage() {
  const { slug = '' } = useParams()

  const hero = useQuery({
    queryKey: ['heroes', 'detail', slug],
    queryFn: ({ signal }) => api.heroes.detail(slug, signal),
    enabled: slug !== '',
    staleTime: 10 * 60 * 1000,
  })

  const trends = useQuery({
    queryKey: ['heroes', 'trends', slug, '7'],
    queryFn: ({ signal }) => api.heroes.trends(slug, '7', signal),
    enabled: slug !== '',
    staleTime: 10 * 60 * 1000,
  })

  const history = useQuery({
    queryKey: ['heroes', 'history', slug],
    queryFn: ({ signal }) => api.heroes.history(slug, signal),
    enabled: slug !== '',
    staleTime: 10 * 60 * 1000,
  })

  if (hero.isPending) return <LoadingView message="Loading the hero…" />

  if (hero.isError) {
    return (
      <div className="space-y-4">
        <BackLink />
        <ErrorView
          message={hero.error instanceof Error ? hero.error.message : 'The hero could not load.'}
          onRetry={() => hero.refetch()}
        />
      </div>
    )
  }

  const data = hero.data
  const trendPoints = trends.data ?? []
  const first = trendPoints[0]
  const last = trendPoints[trendPoints.length - 1]
  const change = first && last ? last.winRate - first.winRate : null

  return (
    <div className="space-y-6">
      <BackLink />

      <header className="flex items-start gap-4">
        <HeroAvatar name={data.name} src={data.portrait ?? data.headImage} size={72} />
        <div className="min-w-0 flex-1">
          <h1 className="font-display text-2xl font-extrabold tracking-tight">{data.name}</h1>
          <p className="text-sm text-text-2">
            {data.roles.length > 0 ? data.roles.join(' · ') : 'Role not reported'}
          </p>
          <p className="text-xs text-muted">
            {data.lanes.length > 0 ? data.lanes.join(' · ') : 'Lane not reported'}
            {data.specialties.length > 0 ? ` · ${data.specialties.join(' · ')}` : ''}
          </p>
        </div>
      </header>

      {data.rankStat ? (
        <div className="grid grid-cols-3 gap-3">
          <StatTile label="Win rate" value={percent(data.rankStat.winRate)} tone="positive" />
          <StatTile label="Ban rate" value={percent(data.rankStat.banRate)} />
          <StatTile label="Pick rate" value={percent(data.rankStat.pickRate)} />
        </div>
      ) : (
        <p className="rounded-card border border-border bg-card px-4 py-3 text-sm text-muted">
          No ranking statistics are available for this hero right now.
        </p>
      )}

      <section>
        <div className="mb-3 flex items-end justify-between gap-4">
          <div>
            <h2 className="font-display text-base font-bold tracking-tight">7-day trend</h2>
            <p className="text-sm text-muted">Live provider observations</p>
          </div>
          {change !== null ? (
            <span
              className={`stat inline-flex items-center gap-1 text-sm font-semibold ${
                change >= 0 ? 'text-positive' : 'text-negative'
              }`}
            >
              {change >= 0 ? <TrendUpIcon size={16} /> : <TrendDownIcon size={16} />}
              {(change * 100).toFixed(2)} pts
            </span>
          ) : null}
        </div>
        {trends.isPending ? (
          <LoadingView message="Loading the trend…" />
        ) : trends.isError ? (
          <ErrorView
            message={
              trends.error instanceof Error ? trends.error.message : 'The trend could not load.'
            }
            onRetry={() => trends.refetch()}
          />
        ) : (
          <Suspense fallback={<LoadingView message="Loading the chart…" />}>
            <TrendChart points={trendPoints} />
          </Suspense>
        )}
      </section>

      <section>
        <div className="mb-3">
          <h2 className="font-display text-base font-bold tracking-tight">Recorded history</h2>
          <p className="text-sm text-muted">
            Daily snapshots this server wrote down while fetching the live rankings
          </p>
        </div>
        {history.isPending ? (
          <LoadingView message="Loading the recorded history…" />
        ) : history.isError ? (
          <ErrorView
            message={
              history.error instanceof Error ? history.error.message : 'The history could not load.'
            }
            onRetry={() => history.refetch()}
          />
        ) : (
          <Suspense fallback={<LoadingView message="Loading the chart…" />}>
            <HistoryChart points={history.data ?? []} />
          </Suspense>
        )}
      </section>

      {data.skills.length > 0 ? (
        <section>
          <h2 className="mb-3 font-display text-base font-bold tracking-tight">Skills</h2>
          <div className="space-y-2">
            {data.skills.map((skill) => (
              <div key={skill.name} className="rounded-card border border-border bg-card p-4">
                <p className="text-sm font-semibold">{skill.name}</p>
                <p className="mt-1 text-sm text-text-2">{skill.description}</p>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {data.strongAgainst.length > 0 || data.weakAgainst.length > 0 ? (
        <section className="grid gap-3 sm:grid-cols-2">
          {data.strongAgainst.length > 0 ? (
            <RelationCard title="Strong against" heroes={data.strongAgainst} tone="positive" />
          ) : null}
          {data.weakAgainst.length > 0 ? (
            <RelationCard title="Weak against" heroes={data.weakAgainst} tone="negative" />
          ) : null}
        </section>
      ) : null}
    </div>
  )
}

function RelationCard({
  title,
  heroes,
  tone,
}: {
  title: string
  heroes: string[]
  tone: 'positive' | 'negative'
}) {
  return (
    <div className="rounded-card border border-border bg-card p-4">
      <p
        className={`text-[11px] font-semibold uppercase tracking-[0.08em] ${
          tone === 'positive' ? 'text-positive' : 'text-negative'
        }`}
      >
        {title}
      </p>
      <ul className="mt-2 space-y-1 text-sm text-text-2">
        {heroes.map((hero) => (
          <li key={hero}>{hero}</li>
        ))}
      </ul>
    </div>
  )
}

function BackLink() {
  return (
    <Link
      to="/heroes"
      className="inline-flex items-center gap-1.5 text-sm font-semibold text-text-2 transition hover:text-accent"
    >
      <ChevronLeftIcon size={16} />
      All heroes
    </Link>
  )
}
