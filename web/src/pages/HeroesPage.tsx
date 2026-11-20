import { useQuery } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { api } from '../lib/api'
import { percent } from '../lib/format'
import { HeroAvatar } from '../components/HeroAvatar'
import { EmptyView, ErrorView, LoadingView } from '../components/StateViews'
import { SearchIcon } from '../components/Icons'

const ROLE_FILTERS = ['all', 'Assassin', 'Fighter', 'Mage', 'Marksman', 'Tank', 'Support']
const LANE_FILTERS = ['all', 'Exp', 'Gold', 'Mid', 'Roam', 'Jungle']

export function HeroesPage() {
  const [search, setSearch] = useState('')
  const [role, setRole] = useState('all')
  const [lane, setLane] = useState('all')

  const heroes = useQuery({
    queryKey: ['heroes', 'catalog'],
    queryFn: ({ signal }) => api.heroes.list(signal),
    staleTime: 10 * 60 * 1000,
  })

  const filtered = useMemo(() => {
    const needle = search.trim().toLowerCase()
    return (heroes.data ?? []).filter((hero) => {
      if (role !== 'all' && !hero.roles.some((value) => value.toLowerCase() === role.toLowerCase()))
        return false
      if (lane !== 'all' && !hero.lanes.some((value) => value.toLowerCase() === lane.toLowerCase()))
        return false
      if (needle && !hero.name.toLowerCase().includes(needle)) return false
      return true
    })
  }, [heroes.data, search, role, lane])

  return (
    <div className="space-y-5">
      <header>
        <h1 className="font-display text-2xl font-extrabold tracking-tight">Heroes</h1>
        <p className="text-sm text-text-2">
          {heroes.data ? `${heroes.data.length} heroes in the current roster` : 'The full roster'}
        </p>
      </header>

      <div className="relative">
        <SearchIcon
          size={18}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted"
        />
        <input
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search heroes"
          aria-label="Search heroes"
          className="w-full rounded-control border border-border bg-card py-2.5 pl-10 pr-3 text-sm outline-none transition focus:border-accent"
        />
      </div>

      <div className="space-y-2">
        <FilterRow
          label="Role"
          options={ROLE_FILTERS}
          value={role}
          onChange={setRole}
        />
        <FilterRow label="Lane" options={LANE_FILTERS} value={lane} onChange={setLane} />
      </div>

      {heroes.isPending ? (
        <LoadingView message="Loading the hero roster…" />
      ) : heroes.isError ? (
        <ErrorView
          message={
            heroes.error instanceof Error ? heroes.error.message : 'The roster could not load.'
          }
          onRetry={() => heroes.refetch()}
        />
      ) : filtered.length === 0 ? (
        <EmptyView
          icon={<SearchIcon size={34} />}
          title="No hero matches"
          message="Try a different search term or clear the role and lane filters."
        />
      ) : (
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((hero) => (
            <Link
              key={hero.id || hero.slug}
              to={`/heroes/${hero.slug}`}
              className="flex items-center gap-3 rounded-card border border-border bg-card p-3 transition hover:border-accent"
            >
              <HeroAvatar name={hero.name} src={hero.headImage} size={44} />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold">{hero.name}</p>
                <p className="truncate text-xs text-muted">
                  {hero.roles.length > 0 ? hero.roles.join(' · ') : 'Role not reported'}
                </p>
                <p className="truncate text-xs text-muted">
                  {hero.lanes.length > 0 ? hero.lanes.join(' · ') : 'Lane not reported'}
                </p>
              </div>
              {hero.tier ? (
                <span className="rounded-full bg-accent-soft px-2 py-0.5 text-[11px] font-bold text-accent">
                  {hero.tier}
                </span>
              ) : null}
            </Link>
          ))}
        </div>
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
  options: string[]
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
          key={option}
          type="button"
          onClick={() => onChange(option)}
          className={`shrink-0 rounded-full px-3 py-1.5 text-xs font-semibold transition ${
            value === option
              ? 'bg-accent text-white'
              : 'border border-border bg-card text-text-2 hover:text-text'
          }`}
        >
          {option === 'all' ? 'All' : option}
        </button>
      ))}
    </div>
  )
}

/** A small helper used by the rankings table too. */
export function winRateLabel(value: number | null | undefined): string {
  return percent(value)
}
