/**
 * Local persistence.
 *
 * Two separate secrets live here and they never mix:
 *
 * - the **app session** token (Google sign-in), used for `/auth/*`;
 * - the **player session** token (consented game-account link), used for
 *   `/players/*`.
 */

const ACCOUNT_TOKEN_KEY = 'mlbb.accountToken'
const PLAYER_TOKEN_KEY = 'mlbb.playerToken'
const FAVOURITES_KEY = 'mlbb.favourites'
const THEME_KEY = 'mlbb.theme'

function read(key: string): string | null {
  try {
    return window.localStorage.getItem(key)
  } catch {
    return null
  }
}

function write(key: string, value: string | null): void {
  try {
    if (value === null) window.localStorage.removeItem(key)
    else window.localStorage.setItem(key, value)
  } catch {
    // Private mode or a blocked storage area: the app still works for the
    // current page view, the session simply is not remembered.
  }
}

export const accountToken = {
  get: () => read(ACCOUNT_TOKEN_KEY),
  set: (token: string | null) => write(ACCOUNT_TOKEN_KEY, token),
}

export const playerToken = {
  get: () => read(PLAYER_TOKEN_KEY),
  set: (token: string | null) => write(PLAYER_TOKEN_KEY, token),
}

export const favourites = {
  get(): string[] {
    const raw = read(FAVOURITES_KEY)
    if (!raw) return []
    try {
      const parsed = JSON.parse(raw)
      return Array.isArray(parsed) ? parsed.filter((item): item is string => typeof item === 'string') : []
    } catch {
      return []
    }
  },
  set(slugs: string[]): void {
    write(FAVOURITES_KEY, JSON.stringify(slugs))
  },
}

export type Theme = 'dark' | 'light'

export const theme = {
  get(): Theme {
    const raw = read(THEME_KEY)
    // The midnight arena is the app's signature look.
    return raw === 'light' ? 'light' : 'dark'
  },
  set(value: Theme): void {
    write(THEME_KEY, value)
    document.documentElement.dataset.theme = value
  },
}
