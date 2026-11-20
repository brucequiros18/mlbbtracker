import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-24 text-center">
      <p className="stat font-display text-4xl font-extrabold text-accent">404</p>
      <h1 className="font-display text-xl font-bold">This page does not exist</h1>
      <p className="max-w-sm text-sm text-text-2">
        The link may be outdated. Head back to the overview and pick up from there.
      </p>
      <Link
        to="/"
        className="rounded-control bg-accent px-5 py-2.5 text-sm font-semibold text-white transition hover:opacity-90"
      >
        Back to the overview
      </Link>
    </div>
  )
}
