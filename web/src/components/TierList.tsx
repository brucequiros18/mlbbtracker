import { Link } from 'react-router-dom'

import { percent } from '../lib/format'
import type { HeroRanking } from '../lib/types'
import { HeroAvatar } from './HeroAvatar'
import { EmptyView } from './StateViews'

/**
 * A tier-list view of the meta rankings: heroes grouped by their wiki-backed
 * tier badge, highest tier first, win rate inside each group.
 *
 * The badge colours are full literal class strings - Tailwind's scanner
 * cannot see interpolated class names.
 */

interface TierStyle {
  label: string
  /** Full literal utility strings, so the scanner picks them up. */
  badge: string
  wr: string
}

const TIER_STYLES: Record<string, TierStyle> = {
  'S+': {
    label: 'S+',
    badge: 'border-tier-splus/40 bg-tier-splus/10 text-tier-splus',
    wr: 'text-tier-splus',
  },
  S: {
    label: 'S',
    badge: 'border-tier-s/40 bg-tier-s/10 text-tier-s',
    wr: 'text-tier-s',
  },
  A: {
    label: 'A',
    badge: 'border-tier-a/40 bg-tier-a/10 text-tier-a',
    wr: 'text-tier-a',
  },
  B: {
    label: 'B',
    badge: 'border-tier-b/40 bg-tier-b/10 text-tier-b',
    wr: 'text-tier-b',
  },
  C: {
    label: 'C',
    badge: 'border-tier-c/40 bg-tier-c/10 text-tier-c',
    wr: 'text-tier-c',
  },
}

const UNKNOWN_STYLE: TierStyle = {
  label: '?',
  badge: 'border-tier-x/40 bg-tier-x/10 text-tier-x',
  wr: 'text-tier-x',
}

const TIER_ORDER = ['S+', 'S', 'A', 'B', 'C']

function styleFor(tier: string | null): TierStyle {
  if (tier && TIER_STYLES[tier]) return TIER_STYLES[tier]
  return { ...UNKNOWN_STYLE, label: tier && tier.trim() !== '' ? tier : '?' }
}

export function TierList({ rows }: { rows: HeroRanking[] }) {
  const groups = new Map<string, HeroRanking[]>()

  for (const row of rows) {
    const key = row.tier && row.tier.trim() !== '' ? row.tier : '?'
    const bucket = groups.get(key)
    if (bucket) bucket.push(row)
    else groups.set(key, [row])
  }

  const orderedTiers = [
    ...TIER_ORDER.filter((tier) => groups.has(tier)),
    ...[...groups.keys()].filter((tier) => !TIER_ORDER.includes(tier)).sort(),
  ]

  if (orderedTiers.length === 0) {
    return (
      <EmptyView
        title="No tiers yet"
        message="The provider has not attached wiki tiers to this window yet."
      />
    )
  }

  return (
    <div className="space-y-3">
      {orderedTiers.map((tier) => {
        const style = styleFor(tier)
        const bucket = [...(groups.get(tier) ?? [])].sort((a, b) => b.winRate - a.winRate)

        return (
          <section
            key={tier}
            className="rounded-card border border-border bg-card p-4"
            aria-label={`Tier ${style.label} - ${bucket.length} heroes`}
          >
            <div className="flex items-center gap-3">
              <span
                className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-control border font-display text-lg font-bold ${style.badge}`}
              >
                {style.label}
              </span>
              <div className="min-w-0">
                <p className="font-display text-base font-bold">{style.label} tier</p>
                <p className="text-xs text-muted">{bucket.length} heroes, best win rate first</p>
              </div>
            </div>

            <ul className="mt-3 flex flex-wrap gap-2">
              {bucket.map((hero) => (
                <li key={hero.id}>
                  <Link
                    to={`/heroes/${hero.slug || hero.id}`}
                    className="flex items-center gap-2 rounded-control border border-border bg-bg-2 py-1.5 pl-1.5 pr-3 transition hover:border-accent"
                  >
                    <HeroAvatar src={hero.headImage} name={hero.name} size={32} />
                    <span className="min-w-0">
                      <span className="block truncate text-sm font-semibold">{hero.name}</span>
                      <span className={`stat block text-xs ${style.wr}`}>
                        {percent(hero.winRate)} WR
                      </span>
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        )
      })}
    </div>
  )
}
