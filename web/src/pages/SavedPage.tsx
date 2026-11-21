import { useQueries, useQuery } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { api } from '../lib/api'
import { useFavourites } from '../lib/useFavourites'
import { percent } from '../lib/format'
import { HeroAvatar } from '../components/HeroAvatar'
import { TierBadge, tierRank } from '../components/TierBadge'
import { TrendDelta } from '../components/TrendDelta'
import { EmptyView, ErrorView, LoadingView } from '../components/StateViews'
import { SavedIcon } from '../components/Icons'

type Sort = 'movement' | 'win_rate' | 'tier' | 'name'

const SORTS: { value: Sort; label: string }[] = [
  { value: 'movement', label: '7d movement' },
  { value: 'win_rate', label: 'Win rate' },
  { value: 'tier', label: 'Tier' },
  { value: 'name', label: 'Name' },
]

const MAX_COMPARE = 3

/**
 * The watchlist: every bookmarked hero with live meta context - current
 * tier, rank position, win rate and the 7-day movement - plus multi-select
 * that hands the heroes to the comparison view.
 */
export function SavedPage() {
  const { slugs, remove, clear } = useFavourites()
  const navigate = useNavigate()
  const [sort, setSort] = useState<Sort>('movement')
  const [selected, setSelected] = useState<string[]>([])

  const rankings = useQuery({
    queryKey: ['heroes', 'rankings', { days: '7', rank: 'all', sort: 'win_rate' }],
    queryFn: ({ signal }) =>
      api.heroes.rankings({ days: '7', rank: 'all', sort: 'win_rate' }, signal),
    staleTime: 5 * 60 * 1000,
  })

  const all = useMemo(() => rankings.data ?? [], [rankings.data])

  // One batched trend query per saved hero; the deltas drive both the
  // movement sort and the per-row chips.
  const trendQueries = useQueries({
    queries: slugs.map((slug) => ({
      queryKey: ['heroes', 'trends', slug, '7'],
      queryFn: ({ signal }: { signal: AbortSignal }) =>
        api.heroes.trends(slug, '7', signal),
      staleTime: 5 * 60 * 1000,
      enabled: slugs.length > 0,
    })),
  })

  const deltas = useMemo(() => {
    const map = new Map<string, number | null>()
    slugs.forEach((slug, index) => {
      const points = trendQueries[index]?.data
      if (points && points.length >= 2) {
        map.set(slug, (points[points.length - 1].winRate - points[0].winRate) * 100)
      } else {
        map.set(slug, null)
      }
    })
    return map
  }, [slugs, trendQueries])

  const movementsLoaded =
    slugs.length > 0 && slugs.every((slug) => deltas.get(slug) !== null && deltas.get(slug) !== undefined)

  const metaAverage = useMemo(() => {
    if (all.length === 0) return null
    return all.reduce((sum, hero) => sum + hero.winRate, 0) / all.length
  }, [all])

  // Win-rate rank position: the rankings arrive sorted by win rate.
  const positionBySlug = useMemo(() => {
    const map = new Map<string, number>()
    all.forEach((hero, index) => map.set(hero.slug, index + 1))
    return map
  }, [all])

  const saved = useMemo(() => {
    const rows = all.filter((hero) => slugs.includes(hero.slug))
    const deltaOf = (slug: string) => deltas.get(slug) ?? Number.NEGATIVE_INFINITY
    const sorters: Record<Sort, (a: (typeof rows)[number], b: (typeof rows)[number]) => number> = {
      movement: (a, b) => deltaOf(b.slug) - deltaOf(a.slug),
      win_rate: (a, b) => b.winRate - a.winRate,
      tier: (a, b) => tierRank(a.tier) - tierRank(b.tier) || b.winRate - a.winRate,
      name: (a, b) => a.name.localeCompare(b.name),
    }
    return [...rows].sort(sorters[sort])
  }, [all, slugs, sort, deltas])

  const missing = slugs.filter((slug) => !saved.some((hero) => hero.slug === slug))

  const summary = useMemo(() => {
    if (saved.length === 0 || metaAverage === null) return null
    const average = saved.reduce((sum, hero) => sum + hero.winRate, 0) / saved.length
    const topTier = saved.filter((hero) => tierRank(hero.tier) <= 1).length
    return {
      average,
      versusMeta: (average - metaAverage) * 100,
      topTier,
    }
  }, [saved, metaAverage])

  const toggleSelected = (slug: string) => {
    setSelected((current) =>
      current.includes(slug)
        ? current.filter((item) => item !== slug)
        : current.length >= MAX_COMPARE
          ? current
          : [...current, slug],
    )
  }

  const compare = () => {
    if (selected.length >= 2) {
      navigate(`/compare?h=${selected.join(',')}`)
    }
  }

  return (
    <div className="space-y-5">
      <header className="flex items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-extrabold tracking-tight">Saved</h1>
          <p className="text-sm text-text-2">
            Your watchlist: live meta context for the heroes you follow
          </p>
        </div>
        {slugs.length > 0 ? (
          <button
            type="button"
            onClick={() => {
              clear()
              setSelected([])
            }}
            className="text-sm font-semibold text-text-2 transition hover:text-negative"
          >
            Clear all
          </button>
        ) : null}
      </header>

      {slugs.length === 0 ? (
        <EmptyView
          icon={<SavedIcon size={34} />}
          title="Nothing saved yet"
          message="Bookmark heroes to watch their tier, win rate and 7-day movement here - and pick up to three for a head-to-head comparison."
          action={
            <Link
              to="/heroes"
              className="rounded-control bg-accent px-4 py-2.5 text-sm font-semibold text-white transition hover:opacity-90"
            >
              Browse the roster
            </Link>
          }
        />
      ) : rankings.isPending ? (
        <LoadingView message="Loading your saved heroes…" />
      ) : rankings.isError ? (
        <ErrorView
          message={
            rankings.error instanceof Error
              ? rankings.error.message
              : 'The rankings could not be loaded.'
          }
          onRetry={() => rankings.refetch()}
        />
      ) : (
        <>
          {summary ? (
            <div className="grid grid-cols-3 gap-2">
              <div className="rounded-card border border-border bg-card p-3 text-center">
                <p className="stat font-display text-xl font-bold">{saved.length}</p>
                <p className="text-xs text-muted">saved</p>
              </div>
              <div className="rounded-card border border-border bg-card p-3 text-center">
                <p className="stat font-display text-xl font-bold">{percent(summary.average)}</p>
                <p className="text-xs text-muted">
                  avg WR{' '}
                  <span
                    className={
                      summary.versusMeta >= 0 ? 'text-positive' : 'text-negative'
                    }
                  >
                    {summary.versusMeta >= 0 ? '+' : ''}
                    {summary.versusMeta.toFixed(1)}pp
                  </span>{' '}
                  vs meta
                </p>
              </div>
              <div className="rounded-card border border-border bg-card p-3 text-center">
                <p className="stat font-display text-xl font-bold text-tier-splus">
                  {summary.topTier}
                </p>
                <p className="text-xs text-muted">in S+/S</p>
              </div>
            </div>
          ) : null}

          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap gap-1.5" role="group" aria-label="Sort saved heroes">
              {SORTS.map((entry) => (
                <button
                  key={entry.value}
                  type="button"
                  onClick={() => setSort(entry.value)}
                  className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
                    sort === entry.value
                      ? 'bg-accent text-white'
                      : 'border border-border bg-card text-text-2 hover:text-text'
                  }`}
                >
                  {entry.label}
                </button>
              ))}
            </div>
            <button
              type="button"
              onClick={compare}
              disabled={selected.length < 2}
              className="rounded-control bg-accent px-4 py-2 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-40"
            >
              Compare{selected.length > 0 ? ` (${selected.length})` : ''}
            </button>
          </div>

          <ul className="space-y-2">
            {saved.map((hero) => {
              const isSelected = selected.includes(hero.slug)
              const versusMeta =
                metaAverage === null ? null : (hero.winRate - metaAverage) * 100

              return (
                <li
                  key={hero.slug}
                  className={`rounded-card border bg-card p-3 transition ${
                    isSelected ? 'border-accent' : 'border-border'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <label className="shrink-0" aria-label={`Select ${hero.name} for comparison`}>
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleSelected(hero.slug)}
                        disabled={!isSelected && selected.length >= MAX_COMPARE}
                        className="h-4 w-4 accent-[var(--accent)]"
                      />
                    </label>
                    <TierBadge tier={hero.tier} size="sm" />
                    <Link
                      to={`/heroes/${hero.slug}`}
                      className="flex min-w-0 flex-1 items-center gap-3"
                    >
                      <HeroAvatar name={hero.name} src={hero.headImage} size={40} />
                      <span className="min-w-0">
                        <span className="block truncate text-sm font-semibold">
                          {hero.name}
                        </span>
                        <span className="stat block text-xs text-muted">
                          #{positionBySlug.get(hero.slug) ?? '?'} of {all.length} by WR
                          {versusMeta !== null
                            ? ` · ${versusMeta >= 0 ? '+' : ''}${versusMeta.toFixed(1)}pp vs meta`
                            : ''}
                        </span>
                      </span>
                    </Link>
                    <span className="shrink-0 text-right">
                      <span className="stat block text-sm font-bold">{percent(hero.winRate)}</span>
                      <TrendDelta delta={deltas.get(hero.slug)} />
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        remove(hero.slug)
                        setSelected((current) => current.filter((item) => item !== hero.slug))
                      }}
                      className="shrink-0 text-xs font-semibold text-muted transition hover:text-negative"
                      aria-label={`Remove ${hero.name} from saved`}
                    >
                      ✕
                    </button>
                  </div>
                </li>
              )
            })}

            {missing.map((slug) => (
              <li
                key={slug}
                className="flex items-center justify-between gap-3 rounded-card border border-border bg-card p-3"
              >
                <span className="text-sm font-semibold capitalize">
                  {slug.replace(/(^|-)(\w)/g, (_, __, c) => ` ${c.toUpperCase()}`)}
                </span>
                <span className="text-xs text-muted">not in the current rankings</span>
                <button
                  type="button"
                  onClick={() => remove(slug)}
                  className="text-xs font-semibold text-muted transition hover:text-negative"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>

          {sort === 'movement' && !movementsLoaded ? (
            <p className="text-xs text-muted" role="status">
              Loading the 7-day movements…
            </p>
          ) : null}

          {selected.length >= 2 ? (
            <p className="text-xs text-muted" role="status">
              {selected.length} of {MAX_COMPARE} selected - Compare opens them side by side.
            </p>
          ) : null}
        </>
      )}
    </div>
  )
}
