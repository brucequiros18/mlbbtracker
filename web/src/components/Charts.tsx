import { useMemo } from 'react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { HistoryPoint, TrendPoint } from '../lib/types'
import { percent } from '../lib/format'

/**
 * Win / ban / pick rates over time.
 *
 * The rates are provider observations, not forecasts. When the provider has
 * nothing for this hero the chart says so instead of drawing a flat line.
 */
export function TrendChart({
  points,
  height = 220,
}: {
  points: TrendPoint[]
  height?: number
}) {
  const chart = useMemo(
    () =>
      points.map((point) => ({
        date: point.date,
        winRate: Number((point.winRate * 100).toFixed(2)),
        banRate: Number((point.banRate * 100).toFixed(2)),
        pickRate: Number((point.pickRate * 100).toFixed(2)),
      })),
    [points],
  )

  if (chart.length === 0) {
    return (
      <p className="rounded-card border border-border bg-card px-4 py-8 text-center text-sm text-muted">
        The provider has no trend data for this hero yet.
      </p>
    )
  }

  return (
    <div className="rounded-card border border-border bg-card p-4">
      <TrendChartSvg chart={chart} height={height} />
    </div>
  )
}

function TrendChartSvg({ chart, height }: { chart: TrendPointDisplay[]; height: number }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={chart} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
        <defs>
          <linearGradient id="winFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity={0.35} />
            <stop offset="100%" stopColor="var(--accent)" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="date" tickLine={false} axisLine={false} minTickGap={24} fontSize={11} />
        <YAxis
          domain={[0, (max: number) => Math.max(10, Math.ceil(max / 10) * 10)]}
          tickLine={false}
          axisLine={false}
          fontSize={11}
          width={42}
          tickFormatter={(value: number) => `${value}%`}
        />
        <Tooltip
          contentStyle={{
            background: 'var(--elevated)',
            border: '1px solid var(--border)',
            borderRadius: 10,
            fontSize: 12,
          }}
          formatter={(value, name) => [
            `${typeof value === 'number' ? value.toFixed(2) : value}%`,
            String(name),
          ]}
        />
        <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
        <Area
          type="monotone"
          dataKey="winRate"
          name="Win rate"
          stroke="var(--accent)"
          strokeWidth={2}
          fill="url(#winFill)"
        />
        <Area
          type="monotone"
          dataKey="banRate"
          name="Ban rate"
          stroke="var(--warning)"
          strokeWidth={1.6}
          fillOpacity={0}
        />
        <Area
          type="monotone"
          dataKey="pickRate"
          name="Pick rate"
          stroke="var(--positive)"
          strokeWidth={1.6}
          fillOpacity={0}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

interface TrendPointDisplay {
  date: string
  winRate: number
  banRate: number
  pickRate: number
}

/**
 * The app's own recorded history.
 *
 * These are observations this server wrote down on the day it fetched the
 * live rankings - not provider data and not a forecast.
 */
export function HistoryChart({ points }: { points: HistoryPoint[] }) {
  if (points.length === 0) {
    return (
      <p className="rounded-card border border-border bg-card px-4 py-8 text-center text-sm text-muted">
        No snapshots recorded yet. They accumulate once per day as the server
        fetches the live rankings.
      </p>
    )
  }

  const first = points[0]
  const last = points[points.length - 1]
  const change = last.winRate - first.winRate

  return (
    <div className="rounded-card border border-border bg-card p-4">
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-muted">
            Recorded win rate
          </p>
          <p className="stat font-display text-2xl font-bold">{percent(last.winRate)}</p>
        </div>
        <p
          className={`stat text-sm font-semibold ${change >= 0 ? 'text-positive' : 'text-negative'}`}
        >
          {change >= 0 ? '+' : ''}
          {(change * 100).toFixed(2)} pts since {first.capturedOn}
        </p>
      </div>
      <HistoryBars points={points} />
    </div>
  )
}

function HistoryBars({ points }: { points: HistoryPoint[] }) {
  const values = points.map((point) => point.winRate)
  const max = Math.max(...values)
  const min = Math.min(...values)
  const span = max - min || 1

  return (
    <div className="flex h-28 items-end gap-1" role="img" aria-label="Recorded win rate per day">
      {points.map((point) => {
        // The bar grows from the bottom of the chart, so a single snapshot
        // still shows a visible mark.
        const height = 12 + ((point.winRate - min) / span) * 88
        return (
          <div key={point.capturedOn} className="group relative flex h-full flex-1 items-end">
            <div
              className="w-full rounded-t bg-accent/80 transition group-hover:bg-accent"
              style={{ height: `${height}%` }}
              title={`${point.capturedOn}: ${percent(point.winRate)}`}
            />
          </div>
        )
      })}
    </div>
  )
}

export interface ComparisonSeries {
  name: string
  colour: string
}

/**
 * The 7-day win-rate trends of two or three heroes overlaid on one line
 * chart. The data arrives date-keyed with one column per hero; colours come
 * from the theme tokens so both modes read correctly.
 */
export function ComparisonChart({
  data,
  series,
  height = 240,
}: {
  data: Array<Record<string, number | string>>
  series: ComparisonSeries[]
  height?: number
}) {
  if (data.length === 0 || series.length === 0) {
    return (
      <p className="rounded-card border border-border bg-card px-4 py-8 text-center text-sm text-muted">
        The provider has no trend data for these heroes yet.
      </p>
    )
  }

  return (
    <div className="rounded-card border border-border bg-card p-4">
      <p className="mb-2 text-sm font-semibold">7-day win-rate trend</p>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={shortDate} />
          <YAxis tick={{ fontSize: 11 }} domain={['auto', 'auto']} unit="%" />
          <Tooltip
            contentStyle={{
              background: 'var(--card)',
              border: '1px solid var(--border)',
              borderRadius: 8,
              color: 'var(--text)',
            }}
            labelStyle={{ color: 'var(--muted)' }}
            formatter={(value) => [`${String(value)}%`]}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {series.map((entry) => (
            <Line
              key={entry.name}
              type="monotone"
              dataKey={entry.name}
              name={entry.name}
              stroke={entry.colour}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 3 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

function shortDate(value: string): string {
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime())
    ? value
    : parsed.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}
