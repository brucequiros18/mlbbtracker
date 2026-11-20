import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { api } from '../lib/api'
import { percent } from '../lib/format'
import type { RankTier, RankWindow, SortField } from '../lib/types'
import { HeroAvatar } from '../components/HeroAvatar'
import { TierList } from '../components/TierList'
import { EmptyView, ErrorView, LoadingView } from '../components/StateViews'

const WINDOWS: RankWindow[] = ['1', '3', '7', '15', '30']
const TIERS: RankTier[] = ['all', 'epic', 'legend', 'mythic', 'honor', 'glory']
const SORTS: { value: SortField; label: string }[] = [
  { value: 'win_rate', label: 'Win rate' },
  { value: 'ban_rate', label: 'Ban rate' },
  { value: 'pick_rate', label: 'Pick rate' },
]

type View = 'tiers' | 'table'

export function RanksPage() {
  const [days, setDays] = useState<RankWindow>('7')
  const [rank, setRank] = useState<RankTier>('all')
  const [sort, setSort] = useState<SortField>('win_rate')
  const [view, setView] = useState<View>('tiers')

  const rankings = useQuery({
    queryKey: ['heroes', 'rankings', { days, rank, sort }],
    queryFn: ({ signal }) => api.heroes.rankings({ days, rank, sort }, signal),
    staleTime: 5 * 60 * 1000,
  })

  const rows = rankings.data ?? []

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-extrabold tracking-tight">Meta rankings</h1>
          <p className="text-sm text-text-2">
            Live win, ban and pick rates from the ranked provider
          </p>
        </div>
        <div
          className="flex rounded-control border border-border bg-card p-1"
          role="tablist"
          aria-label="Rankings view"
        >
          {(['tiers', 'table'] as View[]).map((entry) => (
            <button
              key={entry}
              type="button"
              role="tab"
              aria-selected={view === entry}
              onClick={() => setView(entry)}
              className={`rounded-[6px] px-3 py-1.5 text-sm font-semibold capitalize transition ${
                view === entry ? 'bg-accent text-white' : 'text-text-2 hover:text-text'
              }`}
            >
              {entry === 'tiers' ? 'Tier list' : 'Table'}
            </button>
          ))}
        </div>
      </header>

      <div className="space-y-2">
        <FilterRow
          label="Window"
          options={WINDOWS.map((value) => ({ value, label: `${value}d` }))}
          value={days}
          onChange={(value) => setDays(value as RankWindow)}
        />
        <FilterRow
          label="Rank"
          options={TIERS.map((value) => ({ value, label: value === 'all' ? 'All' : value }))}
          value={rank}
          onChange={(value) => setRank(value as RankTier)}
        />
        <FilterRow
          label="Sort"
          options={SORTS.map((entry) => ({ value: entry.value, label: entry.label }))}
          value={sort}
          onChange={(value) => setSort(value as SortField)}
        />
      </div>

      {rankings.isPending ? (
        <LoadingView message="Fetching the rankings…" />
      ) : rankings.isError ? (
        <ErrorView
          message={
            rankings.error instanceof Error
              ? rankings.error.message
              : 'The rankings could not be loaded.'
          }
          onRetry={() => rankings.refetch()}
        />
      ) : rows.length === 0 ? (
        <EmptyView
          title="No ranking data"
          message="The provider returned no hero statistics for this combination."
        />
      ) : view === 'tiers' ? (
        <TierList rows={rows} />
      ) : (
        <>
          {/* Desktop: a real table. Phones: cards, because a 4-column table
              does not fit. */}
          <div className="hidden overflow-hidden rounded-card border border-border bg-card md:block">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-[11px] uppercase tracking-[0.08em] text-muted">
                  <th className="px-4 py-3 font-semibold">#</th>
                  <th className="px-4 py-3 font-semibold">Hero</th>
                  <th className="px-4 py-3 text-right font-semibold">Win rate</th>
                  <th className="px-4 py-3 text-right font-semibold">Ban rate</th>
                  <th className="px-4 py-3 text-right font-semibold">Pick rate</th>
                  <th className="px-4 py-3 text-right font-semibold">Tier</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((hero, index) => (
                  <tr key={hero.id || hero.slug} className="border-b border-border/60 last:border-0">
                    <td className="stat px-4 py-2.5 text-muted">{index + 1}</td>
                    <td className="px-4 py-2.5">
                      <Link
                        to={`/heroes/${hero.slug}`}
                        className="flex items-center gap-2.5 font-semibold hover:text-accent"
                      >
                        <HeroAvatar name={hero.name} src={hero.headImage} size={28} />
                        {hero.name}
                      </Link>
                    </td>
                    <td className="stat px-4 py-2.5 text-right font-semibold text-positive">
                      {percent(hero.winRate)}
                    </td>
                    <td className="stat px-4 py-2.5 text-right text-text-2">
                      {percent(hero.banRate)}
                    </td>
                    <td className="stat px-4 py-2.5 text-right text-text-2">
                      {percent(hero.pickRate)}
                    </td>
                    <td className="px-4 py-2.5 text-right text-text-2">{hero.tier ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="space-y-2 md:hidden">
            {rows.map((hero, index) => (
              <Link
                key={hero.id || hero.slug}
                to={`/heroes/${hero.slug}`}
                className="flex items-center gap-3 rounded-card border border-border bg-card p-3"
              >
                <span className="stat w-6 shrink-0 text-sm text-muted">{index + 1}</span>
                <HeroAvatar name={hero.name} src={hero.headImage} size={36} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold">{hero.name}</p>
                  <p className="stat text-xs text-muted">
                    ban {percent(hero.banRate)} · pick {percent(hero.pickRate)}
                  </p>
                </div>
                <span className="stat text-sm font-bold text-positive">{percent(hero.winRate)}</span>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function FilterRow({
  label,
  options,
  value,
  onChange,
}: {
  label: string
  options: { value: string; label: string }[]
  value: string
  onChange: (value: string) => void
}) {
  return (
    <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
      <span className="shrink-0 text-[11px] font-semibold uppercase tracking-[0.08em] text-muted">
        {label}
      </span>
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => onChange(option.value)}
          className={`shrink-0 rounded-full px-3 py-1.5 text-xs font-semibold capitalize transition ${
            value === option.value
              ? 'bg-accent text-white'
              : 'border border-border bg-card text-text-2 hover:text-text'
          }`}
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}
