import type {
  Account,
  ApiEnvelope,
  AuthConfig,
  FrequentHero,
  GoogleSignInResult,
  HealthPayload,
  HeroDetail,
  HeroRanking,
  HeroSummary,
  HistoryPoint,
  PlayerMatchesPage,
  PlayerProfile,
  PlayerStats,
  RankTier,
  RankWindow,
  SortField,
  Standing,
  TrendPoint,
} from './types'

/**
 * A failure the server described.
 *
 * Every API error carries a stable `code` (`NOT_FOUND`, `AUTH_REQUIRED`,
 * `PROVIDER_UNAVAILABLE`, ...), so the UI branches on that instead of
 * parsing free-form text.
 */
export class ApiError extends Error {
  readonly code: string
  readonly status: number
  readonly details: string | undefined

  constructor(message: string, code: string, status: number, details?: string) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.details = details
  }
}

/** The API lives on the same origin as the app. */
const API_BASE = '/api/v1'

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  body?: unknown
  token?: string | null
  signal?: AbortSignal
}

/** Unwrap the `{data, meta}` envelope and surface typed failures. */
async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, token, signal } = options

  const headers: Record<string, string> = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (token) headers.Authorization = `Bearer ${token}`

  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      signal,
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    throw new ApiError(
      'Could not reach the server. Check your connection and try again.',
      'NETWORK_ERROR',
      0,
    )
  }

  const payload = await response.json().catch(() => null)

  if (!response.ok) {
    const error = payload as { code?: string; message?: string; details?: string } | null
    throw new ApiError(
      error?.message ?? `The request failed (${response.status}).`,
      error?.code ?? 'UNKNOWN_ERROR',
      response.status,
      error?.details,
    )
  }

  const envelope = payload as ApiEnvelope<T> | null
  if (envelope && typeof envelope === 'object' && 'data' in envelope) {
    return envelope.data
  }

  return payload as T
}

/** Endpoints that answer without the `{data, meta}` envelope. */
async function requestRaw<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, token, signal } = options

  const headers: Record<string, string> = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (token) headers.Authorization = `Bearer ${token}`

  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    signal,
    body: body === undefined ? undefined : JSON.stringify(body),
  })

  const payload = await response.json().catch(() => null)

  if (!response.ok) {
    const error = payload as { code?: string; message?: string } | null
    throw new ApiError(
      error?.message ?? `The request failed (${response.status}).`,
      error?.code ?? 'UNKNOWN_ERROR',
      response.status,
    )
  }

  return payload as T
}

function query(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') search.set(key, String(value))
  }
  const asString = search.toString()
  return asString ? `?${asString}` : ''
}

export const api = {
  heroes: {
    list: (signal?: AbortSignal) => request<HeroSummary[]>('/heroes', { signal }),

    rankings: (
      params: { days?: RankWindow; rank?: RankTier; sort?: SortField },
      signal?: AbortSignal,
    ) =>
      request<HeroRanking[]>(
        `/heroes/rankings${query({
          days: params.days,
          rank: params.rank,
          sort: params.sort,
        })}`,
        { signal },
      ),

    detail: (identifier: string | number, signal?: AbortSignal) =>
      request<HeroDetail>(`/heroes/${encodeURIComponent(identifier)}`, { signal }),

    trends: (identifier: string | number, days: RankWindow = '7', signal?: AbortSignal) =>
      request<TrendPoint[]>(
        `/heroes/${encodeURIComponent(identifier)}/trends${query({ days })}`,
        { signal },
      ),

    history: (identifier: string | number, signal?: AbortSignal) =>
      request<HistoryPoint[]>(`/heroes/${encodeURIComponent(identifier)}/history`, { signal }),
  },

  esports: {
    standings: (league: string, signal?: AbortSignal) =>
      request<Standing[]>(`/esports/${encodeURIComponent(league)}/standings`, { signal }),
  },

  auth: {
    config: (signal?: AbortSignal) => request<AuthConfig>('/auth/config', { signal }),

    signInWithGoogle: (credential: string) =>
      request<GoogleSignInResult>('/auth/google', {
        method: 'POST',
        body: { credential },
      }),

    register: (
      token: string,
      profile: { username: string; mlbbId: string; password: string },
    ) =>
      request<Account>('/auth/register', {
        method: 'POST',
        token,
        body: profile,
      }),

    me: (token: string, signal?: AbortSignal) =>
      request<Account>('/auth/me', { token, signal }),

    updateProfile: (
      token: string,
      profile: {
        username?: string
        mlbbId?: string
        currentPassword: string
        newPassword?: string
      },
    ) =>
      request<Account>('/auth/me', {
        method: 'PATCH',
        token,
        body: profile,
      }),

    logout: (token: string) =>
      request<{ signedOut: boolean }>('/auth/logout', { method: 'POST', token }),
  },

  players: {
    startConnect: (playerId: string, zoneId: string) =>
      request<{ sent: boolean; message: string }>('/players/connect/start', {
        method: 'POST',
        body: { playerId, zoneId },
      }),

    verifyConnect: (playerId: string, zoneId: string, code: string) =>
      request<{ sessionToken: string; player: PlayerProfile }>('/players/connect/verify', {
        method: 'POST',
        body: { playerId, zoneId, code },
      }),

    disconnect: (token: string) =>
      request<{ disconnected: boolean }>('/players/disconnect', { method: 'POST', token }),

    profile: (token: string, signal?: AbortSignal) =>
      request<PlayerProfile>('/players/me/profile', { token, signal }),

    stats: (token: string, signal?: AbortSignal) =>
      request<PlayerStats>('/players/me/stats', { token, signal }),

    matches: (token: string, limit = 20, cursor?: string | null, signal?: AbortSignal) =>
      request<PlayerMatchesPage>(
        `/players/me/matches${query({ limit, cursor: cursor ?? undefined })}`,
        { token, signal },
      ),

    frequentHeroes: (token: string, limit = 10, signal?: AbortSignal) =>
      request<FrequentHero[]>(`/players/me/heroes${query({ limit })}`, { token, signal }),
  },

  health: {
    overview: (signal?: AbortSignal) => requestRaw<HealthPayload>('/health', { signal }),
  },
}
