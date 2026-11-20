import { useCallback, useEffect, useState } from 'react'

import { favourites } from '../lib/storage'

/**
 * The player's saved heroes.
 *
 * Stored locally in the browser - there is no server-side bookmark, so the
 * list stays on the device that created it.
 */
export function useFavourites() {
  const [slugs, setSlugs] = useState<string[]>(() => favourites.get())

  useEffect(() => {
    favourites.set(slugs)
  }, [slugs])

  const toggle = useCallback((slug: string) => {
    setSlugs((current) =>
      current.includes(slug) ? current.filter((item) => item !== slug) : [...current, slug],
    )
  }, [])

  const remove = useCallback((slug: string) => {
    setSlugs((current) => current.filter((item) => item !== slug))
  }, [])

  const clear = useCallback(() => setSlugs([]), [])

  return { slugs, toggle, remove, clear, isSaved: (slug: string) => slugs.includes(slug) }
}
