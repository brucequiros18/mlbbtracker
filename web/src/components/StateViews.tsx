import type { ReactNode } from 'react'

import { RefreshIcon, WifiOffIcon } from './Icons'

/** Skeleton placeholder used while data loads. */
export function LoadingView({ message }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
      <span className="h-7 w-7 animate-spin rounded-full border-2 border-accent border-t-transparent" />
      {message ? <p className="text-sm text-text-2">{message}</p> : null}
    </div>
  )
}

/** Empty-state placeholder with a title and a description. */
export function EmptyView({
  icon,
  title,
  message,
  action,
}: {
  icon?: ReactNode
  title: string
  message: string
  action?: ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 px-6 py-16 text-center">
      {icon ? <span className="text-muted">{icon}</span> : null}
      <h3 className="font-display text-lg font-bold">{title}</h3>
      <p className="max-w-md text-sm text-text-2">{message}</p>
      {action ? <div className="pt-2">{action}</div> : null}
    </div>
  )
}

/** Error-state placeholder with a retry action. */
export function ErrorView({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <EmptyView
      icon={<WifiOffIcon size={34} />}
      title="Something went wrong"
      message={message}
      action={
        onRetry ? (
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex items-center gap-2 rounded-control bg-accent px-4 py-2.5 text-sm font-semibold text-white transition hover:opacity-90"
          >
            <RefreshIcon size={16} />
            Try again
          </button>
        ) : undefined
      }
    />
  )
}

/** A short note about the freshness or limits of what is on screen. */
export function NoteBanner({ children }: { children: ReactNode }) {
  return (
    <p className="rounded-control border border-border bg-bg-2 px-4 py-3 text-sm text-text-2">
      {children}
    </p>
  )
}
