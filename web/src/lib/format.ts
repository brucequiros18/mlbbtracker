/** Small helpers shared across the app. */

/** A rate between 0 and 1 as a percentage: 0.5846 -> "58.5%". */
export function percent(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return `${(value * 100).toFixed(digits)}%`
}

/** A rate as a percentage with no decimals: 0.5846 -> "58%". */
export function percentWhole(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return `${Math.round(value * 100)}%`
}

/** A count, or an em dash when the provider did not report one. */
export function count(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return new Intl.NumberFormat('en-US').format(value)
}

/** Hours as "12.4 h", or an em dash. */
export function hours(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return `${value.toFixed(1)} h`
}

/** "2026-11-19" -> "19 Nov". */
export function shortDate(value: string | null | undefined): string {
  if (!value) return '—'
  const parsed = new Date(`${value}T00:00:00Z`)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' })
}

/** An ISO timestamp -> "19 Nov 2026, 11:32". */
export function dateTime(value: string | null | undefined): string {
  if (!value) return '—'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/** A signed delta: 0.012 -> "+1.2%". */
export function delta(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  const points = value * 100
  return `${points >= 0 ? '+' : ''}${points.toFixed(digits)}%`
}

/** Turn a hero name into a URL slug that matches the API. */
export function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '')
}
