import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { api } from '../lib/api'
import { useFavourites } from '../lib/useFavourites'
import { percent } from '../lib/format'
import { HeroAvatar } from '../components/HeroAvatar'
import { EmptyView, ErrorView, LoadingView } from '../components/StateViews'
import { SavedIcon } from '../components/Icons'

export function SavedPage() {
  const { slugs, remove, clear } = useFavourites()

  const rankings = useQuery({
    queryKey: ['heroes', 'rankings', { days: '7', rank: 'all', sort: 'win_rate' }],
    queryFn: ({ signal }) => api.heroes.rankings({ days: '7', rank: 'all', sort: 'win_rate' }, signal),
    staleTime: 5 * 60 * 1000,
  })

  const saved = (rankings.data ?? []).filter((hero) => slugs.includes(hero.slug))

  // A saved hero that has left the roster still deserves a row, even though
  // the provider no longer ranks it.
  const missing = slugs.filter((slug) => !saved.some((hero) => hero.slug === slug))

  return (
    <div className="space-y-5">
      <header className="flex items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-extrabold tracking-tight">Saved</h1>
          <p className="text-sm text-text-2">
            {slugs.length === 0
              ? 'Heroes you bookmark stay on this device'
              : `${slugs.length} hero${slugs.length === 1 ? '' : 'es'} bookmarked on this device`}
          </p>
        </div>
        {slugs.length > 0 ? (
          <button
            type="button"
            onClick={clear}
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
          message="Open a hero and bookmark it to keep it here for quick access."
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
        <ul className="space-y-2">
          {saved.map((hero) => (
            <li
              key={hero.slug}
              className="flex items-center gap-3 rounded-card border border-border bg-card p-3"
            >
              <Link to={`/heroes/${hero.slug}`} className="flex min-w-0 flex-1 items-center gap-3">
                <HeroAvatar name={hero.name} src={hero.headImage} size={40} />
                <span className="min-w-0">
                  <span className="block truncate text-sm font-semibold">{hero.name}</span>
                  <span className="stat block text-xs text-muted">
                    ban {percent(hero.banRate)} · pick {percent(hero.pickRate)}
                  </span>
                </span>
              </Link>
              <span className="stat shrink-0 text-sm font-bold text-positive">
                {percent(hero.winRate)}
              </span>
              <button
                type="button"
                onClick={() => remove(hero.slug)}
                className="shrink-0 text-xs font-semibold text-muted transition hover:text-negative"
              >
                Remove
              </button>
            </li>
          ))}

          {missing.map((slug) => (
            <li
              key={slug}
              className="flex items-center justify-between gap-3 rounded-card border border-border bg-card p-3"
            >
              <span className="text-sm font-semibold capitalize">{slug.replace(/(^|-)(\w)/g, (_, __, c) => ` ${c.toUpperCase()}`)}</span>
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
      )}
    </div>
  )
}
