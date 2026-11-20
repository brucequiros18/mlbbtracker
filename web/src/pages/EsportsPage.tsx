import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { api } from '../lib/api'
import type { League } from '../lib/types'
import { EmptyView, ErrorView, LoadingView } from '../components/StateViews'
import { TrophyIcon } from '../components/Icons'

const LEAGUES: { value: League; label: string }[] = [
  { value: 'id', label: 'MPL Indonesia' },
  { value: 'ph', label: 'MPL Philippines' },
  { value: 'my', label: 'MPL Malaysia' },
  { value: 'kh', label: 'MPL Cambodia' },
]

export function EsportsPage() {
  const [league, setLeague] = useState<League>('id')

  const standings = useQuery({
    queryKey: ['esports', league],
    queryFn: ({ signal }) => api.esports.standings(league, signal),
    staleTime: 10 * 60 * 1000,
  })

  const rows = standings.data ?? []

  return (
    <div className="space-y-5">
      <header>
        <h1 className="font-display text-2xl font-extrabold tracking-tight">Esports</h1>
        <p className="text-sm text-text-2">Regular-season standings for the professional leagues</p>
      </header>

      <div className="flex gap-2 overflow-x-auto no-scrollbar">
        {LEAGUES.map((entry) => (
          <button
            key={entry.value}
            type="button"
            onClick={() => setLeague(entry.value)}
            className={`shrink-0 rounded-full px-4 py-2 text-sm font-semibold transition ${
              league === entry.value
                ? 'bg-accent text-white'
                : 'border border-border bg-card text-text-2 hover:text-text'
            }`}
          >
            {entry.label}
          </button>
        ))}
      </div>

      {standings.isPending ? (
        <LoadingView message="Loading the standings…" />
      ) : standings.isError ? (
        <ErrorView
          message={
            standings.error instanceof Error
              ? standings.error.message
              : 'The standings could not be loaded.'
          }
          onRetry={() => standings.refetch()}
        />
      ) : rows.length === 0 ? (
        <EmptyView
          icon={<TrophyIcon size={34} />}
          title="No standings yet"
          message="The provider has not published a table for this league."
        />
      ) : (
        <div className="overflow-hidden rounded-card border border-border bg-card">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-[11px] uppercase tracking-[0.08em] text-muted">
                <th className="px-3 py-3 font-semibold">#</th>
                <th className="px-3 py-3 font-semibold">Team</th>
                <th className="px-3 py-3 text-right font-semibold">MP</th>
                <th className="hidden px-3 py-3 text-right font-semibold sm:table-cell">W-L</th>
                <th className="px-3 py-3 text-right font-semibold">GW-L</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.teamCode || row.rank} className="border-b border-border/60 last:border-0">
                  <td className="stat px-3 py-2.5 font-semibold text-muted">{row.rank}</td>
                  <td className="px-3 py-2.5">
                    <span className="flex items-center gap-2.5">
                      {row.logo ? (
                        <img
                          src={row.logo}
                          alt=""
                          loading="lazy"
                          className="h-6 w-6 rounded bg-elevated object-contain"
                          onError={(event) => {
                            event.currentTarget.style.display = 'none'
                          }}
                        />
                      ) : null}
                      <span className="min-w-0">
                        <span className="block truncate font-semibold">{row.teamName}</span>
                        <span className="block text-xs text-muted">{row.teamCode}</span>
                      </span>
                    </span>
                  </td>
                  <td className="stat px-3 py-2.5 text-right">{row.matchPoint}</td>
                  <td className="stat hidden px-3 py-2.5 text-right text-text-2 sm:table-cell">
                    {row.matchWins}-{row.matchLosses}
                  </td>
                  <td className="stat px-3 py-2.5 text-right text-text-2">
                    {row.gameWins}-{row.gameLosses}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-xs text-muted">
        Standings come from the Rone Arena community API. Team marks belong to their owners.
      </p>
    </div>
  )
}
