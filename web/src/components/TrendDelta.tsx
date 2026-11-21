/**
 * The 7-day win-rate movement for one hero, e.g. "+1.2" in green or "-0.8"
 * in red. Pure presentation - the caller supplies the computed delta (the
 * watchlist loads its trends in one batch).
 */
export function TrendDelta({ delta }: { delta: number | null | undefined }) {
  if (delta === null || delta === undefined) {
    return (
      <span className="text-xs text-muted" title="No trend data yet">
        —
      </span>
    )
  }

  if (Math.abs(delta) < 0.05) {
    return <span className="text-xs text-muted">±0.0</span>
  }

  const rising = delta > 0

  return (
    <span
      className={`stat inline-flex items-center gap-0.5 text-xs font-semibold ${
        rising ? 'text-positive' : 'text-negative'
      }`}
      title="Win-rate change over the last 7 days"
    >
      {rising ? '▲' : '▼'} {Math.abs(delta).toFixed(1)}
    </span>
  )
}
