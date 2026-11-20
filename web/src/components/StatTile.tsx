import type { ReactNode } from 'react'

/** A labelled number. The value uses tabular figures so columns align. */
export function StatTile({
  label,
  value,
  hint,
  tone = 'default',
}: {
  label: string
  value: ReactNode
  hint?: ReactNode
  tone?: 'default' | 'positive' | 'negative' | 'accent'
}) {
  const toneClass = {
    default: 'text-text',
    positive: 'text-positive',
    negative: 'text-negative',
    accent: 'text-accent',
  }[tone]

  return (
    <div className="rounded-card border border-border bg-card px-4 py-3">
      <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-muted">{label}</p>
      <p className={`stat mt-1 font-display text-xl font-bold ${toneClass}`}>{value}</p>
      {hint ? <p className="mt-0.5 text-xs text-muted">{hint}</p> : null}
    </div>
  )
}

/** A section heading with an optional action on the right. */
export function SectionHeader({
  title,
  subtitle,
  action,
}: {
  title: string
  subtitle?: string
  action?: ReactNode
}) {
  return (
    <div className="mb-3 flex items-end justify-between gap-4">
      <div>
        <h2 className="font-display text-base font-bold tracking-tight">{title}</h2>
        {subtitle ? <p className="text-sm text-muted">{subtitle}</p> : null}
      </div>
      {action}
    </div>
  )
}
