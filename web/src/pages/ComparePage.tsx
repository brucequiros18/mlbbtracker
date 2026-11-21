import { useQueries, useQuery } from '@tanstack/react-query'
import { Suspense, lazy, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { api } from '../lib/api'
import { percent } from '../lib/format'
import { HeroAvatar } from '../components/HeroAvatar'
import { TierBadge } from '../components/TierBadge'
import { EmptyView, ErrorView, LoadingView } from '../components/StateViews'
import { CloseIcon, SearchIcon } from '../components/Icons'

const ComparisonChart = lazy(() =>
  import('../components/Charts').then((module) => ({
    default: module.ComparisonChart,
  })),
)

const MAX_COMPARE = 3

/** Line colours for the overlaid trends - theme tokens, distinct per hero. */
const LINE_COLOURS = ['var(--accent)', 'var(--positive)', 'var(--warning)']

/**
 * Head-to-head comparison for two or three heroes: tier, roles, live rates
 * and their 7-day win-rate trends overlaid on one chart. The roster comes
 * from the rankings query; the selection lives in the URL (`?h=a,b,c`) so a
 * comparison is shareable.
 */
export function ComparePage() {
  const [params, setParams] = useSearchParams()
  const [search, setSearch] = useState('')

  const rankings = useQuery({
    queryKey: ['heroes', 'rankings', { days: '7', rank: 'all', sort: 'win_rate' }],
    queryFn: ({ signal }) =>
      api.heroes.rankings({ days: '7', rank: 'all', sort: 'win_rate' }, signal),
    staleTime: 5 * 60 * 1000,
  })

  const all = useMemo(() => rankings.data ?? [], [rankings.data])
  const selected = useMemo(
    () => (params.get('h') ?? '').split(',').filter((slug) => slug !== '').slice(0, MAX_COMPARE),
    [params],
  )

  const roster = useMemo(() => {
    const needle = search.trim().toLowerCase()
    return all
      .filter((hero) => !selected.includes(hero.slug))
      .filter(
        (hero) => needle === '' || hero.name.toLowerCase().includes(needle),
      )
      .slice(0, 8)
  }, [all, search, selected])

  const pick = (slug: string) => {
    if (selected.length >= MAX_COMPARE || selected.includes(slug)) return
    setParams({ h: [...selected, slug].join(',') }, { replace: true })
    setSearch('')
  }

  const unpick = (slug: string) => {
    setParams({ h: selected.filter((item) => item !== slug).join(',') }, { replace: true })
  }

  const rowsBySlug = useMemo(() => {
    const map = new Map<string, (typeof all)[number]>()
    all.forEach((hero) => map.set(hero.slug, hero))
    return map
  }, [all])

  const detailQueries = useQueries({
    queries: selected.map((slug) => ({
      queryKey: ['heroes', 'detail', slug],
      queryFn: ({ signal }: { signal: AbortSignal }) => api.heroes.detail(slug, signal),
      staleTime: 10 * 60 * 1000,
    })),
  })

  const trendQueries = useQueries({
    queries: selected.map((slug) => ({
      queryKey: ['heroes', 'trends', slug, '7'],
      queryFn: ({ signal }: { signal: AbortSignal }) => api.heroes.trends(slug, '7', signal),
      staleTime: 5 * 60 * 1000,
    })),
  })

  const chart = useMemo(() => {
    const byDate = new Map<string, Record<string, number | string>>()
    selected.forEach((slug, index) => {
      const hero = rowsBySlug.get(slug)
      const points = trendQueries[index]?.data ?? []
      points.forEach((point) => {
        const row = byDate.get(point.date) ?? { date: point.date }
        if (hero) row[hero.name] = Number((point.winRate * 100).toFixed(2))
        byDate.set(point.date, row)
      })
    })
    return [...byDate.values()].sort((a, b) => String(a.date).localeCompare(String(b.date)))
  }, [selected, rowsBySlug, trendQueries])

  const chartReady = chart.length > 0 && selected.every((_, index) => trendQueries[index]?.isSuccess)

  const pickable = all.length > 0

  return (
    <div className="space-y-5">
      <header>
        <h1 className="font-display text-2xl font-extrabold tracking-tight">Compare</h1>
        <p className="text-sm text-text-2">
          Side by side: tier, live rates and the 7-day win-rate trend
        </p>
      </header>

      {selected.length > 0 ? (
        <div className="flex flex-wrap items-center gap-2">
          {selected.map((slug) => {
            const hero = rowsBySlug.get(slug)
            return (
              <span
                key={slug}
                className="flex items-center gap-2 rounded-full border border-border bg-card py-1 pl-1 pr-2 text-sm font-semibold"
              >
                <HeroAvatar name={hero?.name ?? slug} src={hero?.headImage} size={24} />
                <span className="max-w-36 truncate">{hero?.name ?? slug}</span>
                <button
                  type="button"
                  onClick={() => unpick(slug)}
                  aria-label={`Remove ${hero?.name ?? slug} from the comparison`}
                  className="text-muted transition hover:text-negative"
                >
                  <CloseIcon size={14} />
                </button>
              </span>
            )
          })}
          <span className="text-xs text-muted">
            {selected.length} of {MAX_COMPARE}
          </span>
        </div>
      ) : null}

      {pickable ? (
        <div className="rounded-card border border-border bg-card p-3">
          <label className="flex items-center gap-2 rounded-control border border-border bg-bg-2 px-3 py-2">
            <SearchIcon size={16} className="shrink-0 text-muted" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder={
                selected.length >= MAX_COMPARE
                  ? `Remove a hero to pick another (max ${MAX_COMPARE})`
                  : 'Search a hero to compare…'
              }
              disabled={selected.length >= MAX_COMPARE}
              className="w-full bg-transparent text-sm outline-none placeholder:text-muted"
            />
          </label>
          {search.trim() !== '' && selected.length < MAX_COMPARE ? (
            <ul className="mt-2 flex flex-wrap gap-2">
              {roster.map((hero) => (
                <li key={hero.id}>
                  <button
                    type="button"
                    onClick={() => pick(hero.slug)}
                    className="flex items-center gap-2 rounded-control border border-border bg-bg-2 py-1 pl-1 pr-2.5 text-sm font-semibold transition hover:border-accent"
                  >
                    <HeroAvatar src={hero.headImage} name={hero.name} size={24} />
                    {hero.name}
                  </button>
                </li>
              ))}
              {roster.length === 0 ? (
                <li className="px-1 py-1 text-sm text-muted">No hero matches that name.</li>
              ) : null}
            </ul>
          ) : null}
        </div>
      ) : rankings.isPending ? (
        <LoadingView message="Loading the roster…" />
      ) : rankings.isError ? (
        <ErrorView
          message={
            rankings.error instanceof Error
              ? rankings.error.message
              : 'The roster could not be loaded.'
          }
          onRetry={() => rankings.refetch()}
        />
      ) : null}

      {selected.length === 0 ? (
        <EmptyView
          title="Pick heroes to compare"
          message={`Search above, or select saved heroes from the watchlist - up to ${MAX_COMPARE} side by side.`}
        />
      ) : selected.length === 1 ? (
        <EmptyView
          title="One more hero"
          message="A comparison needs at least two heroes - search above to add another."
        />
      ) : (
        <>
          {chartReady ? (
            <Suspense fallback={<LoadingView message="Loading the chart." />}>
              <ComparisonChart
                data={chart}
                series={selected.map((slug, index) => ({
                  name: rowsBySlug.get(slug)?.name ?? slug,
                  colour: LINE_COLOURS[index % LINE_COLOURS.length],
                }))}
              />
            </Suspense>
          ) : (
            <LoadingView message="Loading the trends…" />
          )}

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {selected.map((slug, index) => {
              const row = rowsBySlug.get(slug)
              const detail = detailQueries[index]?.data
              const pending = detailQueries[index]?.isPending

              if (!row || pending) {
                return (
                  <div
                    key={slug}
                    className="rounded-card border border-border bg-card p-4"
                  >
                    <LoadingView message="Loading…" />
                  </div>
                )
              }

              return (
                <section key={slug} className="rounded-card border border-border bg-card p-4">
                  <div className="flex items-center gap-3">
                    <HeroAvatar name={row.name} src={row.headImage} size={44} />
                    <div className="min-w-0">
                      <Link
                        to={`/heroes/${row.slug}`}
                        className="block truncate font-display text-base font-bold hover:text-accent"
                      >
                        {row.name}
                      </Link>
                      <p className="text-xs text-muted">
                        {detail?.roles?.length ? detail.roles.join(' · ') : 'Roles not published'}
                      </p>
                    </div>
                    <span className="ml-auto">
                      <TierBadge tier={row.tier} size="sm" />
                    </span>
                  </div>

                  <dl className="mt-3 space-y-1.5 text-sm">
                    <StatRow
                      label="Win rate"
                      value={percent(row.winRate)}
                      best={isBest(row.winRate, selected.map((s) => rowsBySlug.get(s)?.winRate ?? -1))}
                    />
                    <StatRow
                      label="Ban rate"
                      value={percent(row.banRate)}
                      best={isBest(row.banRate, selected.map((s) => rowsBySlug.get(s)?.banRate ?? -1))}
                    />
                    <StatRow
                      label="Pick rate"
                      value={percent(row.pickRate)}
                      best={isBest(row.pickRate, selected.map((s) => rowsBySlug.get(s)?.pickRate ?? -1))}
                    />
                  </dl>

                  {detail ? (
                    <div className="mt-3 space-y-2 border-t border-border pt-3 text-xs text-text-2">
                      <p>
                        <span className="font-semibold text-text">Strong vs:</span>{' '}
                        {detail.strongAgainst.length > 0
                          ? detail.strongAgainst.slice(0, 4).join(', ')
                          : 'not published'}
                      </p>
                      <p>
                        <span className="font-semibold text-text">Weak vs:</span>{' '}
                        {detail.weakAgainst.length > 0
                          ? detail.weakAgainst.slice(0, 4).join(', ')
                          : 'not published'}
                      </p>
                    </div>
                  ) : null}
                </section>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}

function StatRow({ label, value, best }: { label: string; value: string; best: boolean }) {
  return (
    <div className="flex items-center justify-between">
      <dt className="text-text-2">{label}</dt>
      <dd className={`stat font-semibold ${best ? 'text-accent' : ''}`}>{value}</dd>
    </div>
  )
}

function isBest(value: number, all: number[]): boolean {
  return value === Math.max(...all) && all.filter((item) => item === value).length === 1
}
