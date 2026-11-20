import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { api } from '../lib/api'
import {
  SEASON_CHAMPIONS,
  SEASON_HISTORY,
  VERIFIED_ON,
  WORLD_CHAMPION,
  type SeasonResult,
} from '../lib/champions'
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
        <p className="text-sm text-text-2">Standings, grand finals and champions - verified results</p>
      </header>

      <WorldChampionCard />

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

      <ChampionPanel league={league} />


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

/** The world championship, above every league - the peak of the season. */
function WorldChampionCard() {
  return (
    <section className="relative overflow-hidden rounded-card border border-warning/40 bg-warning/10 p-5">
      <div className="flex items-start gap-4">
        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-control border border-warning/40 bg-warning/15 text-warning">
          <TrophyIcon size={26} />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-[0.08em] text-warning">
            {WORLD_CHAMPION.event} · {WORLD_CHAMPION.venue}
          </p>
          <p className="mt-1 font-display text-xl font-bold">
            {WORLD_CHAMPION.champion}{' '}
            <span className="stat text-base font-semibold text-text-2">
              won {WORLD_CHAMPION.score} vs {WORLD_CHAMPION.runnerUp}
            </span>
          </p>
          <p className="mt-1 text-sm text-text-2">{WORLD_CHAMPION.note}</p>
          <p className="mt-2 text-xs text-muted">
            Grand final {WORLD_CHAMPION.concluded} ·{' '}
            <a
              href={WORLD_CHAMPION.source}
              target="_blank"
              rel="noreferrer"
              className="underline decoration-dotted underline-offset-4 hover:text-text-2"
            >
              Liquipedia
            </a>
          </p>
        </div>
      </div>
    </section>
  )
}

/**
 * The grand final is the last node of the playoff bracket: champion vs
 * runner-up with the series score. Recent finals are listed below it - a
 * match-by-match bracket is not published by the standings provider, so only
 * verified results are shown.
 */
function ChampionPanel({ league }: { league: League }) {
  const latest = SEASON_CHAMPIONS[league]
  const history = SEASON_HISTORY[league]

  return (
    <section className="rounded-card border border-border bg-card p-5">
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-control border border-warning/40 bg-warning/15 text-warning">
          <TrophyIcon size={22} />
        </span>
        <div>
          <p className="font-display text-base font-bold">{latest.season} champions</p>
          <p className="text-xs text-muted">Grand final - the last stop of the playoff bracket</p>
        </div>
      </div>

      <GrandFinal result={latest} />

      {history.length > 1 ? (
        <ul className="mt-4 space-y-2 border-t border-border pt-4">
          {history
            .slice()
            .reverse()
            .slice(1)
            .map((entry) => (
              <li key={entry.season} className="flex flex-wrap items-baseline gap-x-2 text-sm">
                <span className="font-semibold text-text-2">{entry.season}</span>
                <span className="font-semibold">{entry.champion}</span>
                <span className="stat text-text-2">
                  {entry.score} vs {entry.runnerUp}
                </span>
                <span className="text-xs text-muted">· {entry.concluded}</span>
              </li>
            ))}
        </ul>
      ) : null}

      <p className="mt-4 border-t border-border pt-3 text-xs text-muted">
        Results verified against official announcements and Liquipedia on {VERIFIED_ON}.
        Match-by-match playoff logs are not published by the standings provider, so only
        verified grand finals are listed.
      </p>
    </section>
  )
}

function GrandFinal({ result }: { result: SeasonResult }) {
  return (
    <div className="mt-4 grid grid-cols-[1fr_auto_1fr] items-center gap-3 rounded-control border border-border bg-bg-2 p-4">
      <div className="min-w-0 text-right">
        <p className="text-xs font-semibold uppercase tracking-[0.08em] text-warning">
          Champion
        </p>
        <p className="mt-0.5 truncate font-display text-lg font-bold">{result.champion}</p>
      </div>
      <div className="px-2 text-center">
        <p className="stat font-display text-2xl font-bold text-accent">{result.score}</p>
        <p className="mt-0.5 whitespace-nowrap text-xs text-muted">{result.concluded}</p>
      </div>
      <div className="min-w-0">
        <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">
          Runner-up
        </p>
        <p className="mt-0.5 truncate font-display text-lg font-semibold text-text-2">
          {result.runnerUp}
        </p>
      </div>
    </div>
  )
}
