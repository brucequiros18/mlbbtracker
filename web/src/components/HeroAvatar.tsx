import { useState } from 'react'

/**
 * A hero portrait.
 *
 * The image comes from the provider, so it can be missing or broken - the
 * fallback shows the hero's initials rather than an empty box.
 */
export function HeroAvatar({
  name,
  src,
  size = 40,
  className = '',
}: {
  name: string
  src: string | null | undefined
  size?: number
  className?: string
}) {
  const [failed, setFailed] = useState(false)
  const initials = name
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join('')

  if (!src || failed) {
    return (
      <div
        className={`flex shrink-0 items-center justify-center rounded-full bg-elevated font-display font-bold text-text-2 ${className}`}
        style={{ width: size, height: size, fontSize: Math.round(size * 0.36) }}
        aria-hidden="true"
      >
        {initials || '?'}
      </div>
    )
  }

  return (
    <img
      src={src}
      alt=""
      loading="lazy"
      decoding="async"
      width={size}
      height={size}
      onError={() => setFailed(true)}
      className={`shrink-0 rounded-full bg-elevated object-cover ${className}`}
      style={{ width: size, height: size }}
    />
  )
}
