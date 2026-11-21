/**
 * The wiki-backed meta tier badge, shared by the tier list, tables and the
 * watchlist.
 *
 * Colours are theme tokens (deep variants on light, bright on dark) and the
 * utility strings are full literals - Tailwind's scanner cannot see
 * interpolated class names.
 */

export interface TierStyle {
  label: string
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

export function tierStyle(tier: string | null | undefined): TierStyle {
  if (tier && TIER_STYLES[tier]) return TIER_STYLES[tier]
  return { ...UNKNOWN_STYLE, label: tier && tier.trim() !== '' ? tier : '?' }
}

/** Canonical tier sort order; unknown tiers sink to the bottom. */
export function tierRank(tier: string | null | undefined): number {
  const order = ['S+', 'S', 'A', 'B', 'C']
  if (tier && order.includes(tier)) return order.indexOf(tier)
  return order.length
}

export function TierBadge({
  tier,
  size = 'md',
}: {
  tier: string | null | undefined
  size?: 'sm' | 'md'
}) {
  const style = tierStyle(tier)
  const box = size === 'sm' ? 'h-7 w-7 text-sm' : 'h-10 w-10 text-lg'

  return (
    <span
      className={`flex shrink-0 items-center justify-center rounded-control border font-display font-bold ${box} ${style.badge}`}
      aria-label={`Tier ${style.label}`}
    >
      {style.label}
    </span>
  )
}
