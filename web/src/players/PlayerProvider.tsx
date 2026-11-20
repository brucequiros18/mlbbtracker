import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import { api, ApiError } from '../lib/api'
import { playerToken } from '../lib/storage'
import type { PlayerProfile } from '../lib/types'

/**
 * The connected game account.
 *
 * A separate session from the Google app account: it is created by
 * exchanging the one-time code from the player's in-game mailbox. The
 * provider token stays on the server - the browser only ever holds the
 * opaque session key.
 */
interface PlayerContextValue {
  token: string | null
  profile: PlayerProfile | null
  status: 'signed-out' | 'connecting' | 'connected'
  connect: (playerId: string, zoneId: string, code: string) => Promise<PlayerProfile>
  disconnect: () => Promise<void>
  refresh: () => Promise<void>
}

const PlayerContext = createContext<PlayerContextValue | null>(null)

export function PlayerProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [token, setToken] = useState<string | null>(() => playerToken.get())
  const [profile, setProfile] = useState<PlayerProfile | null>(null)

  const profileQuery = useQuery({
    queryKey: ['player', 'profile', token],
    queryFn: ({ signal }) => api.players.profile(token as string, signal),
    enabled: token !== null,
    staleTime: 60 * 1000,
    retry: false,
  })

  const connect = useCallback(
    async (playerId: string, zoneId: string, code: string) => {
      const result = await api.players.verifyConnect(playerId, zoneId, code)
      playerToken.set(result.sessionToken)
      setToken(result.sessionToken)
      setProfile(result.player)
      await queryClient.invalidateQueries({ queryKey: ['player'] })
      return result.player
    },
    [queryClient],
  )

  const disconnect = useCallback(async () => {
    const current = token
    playerToken.set(null)
    setToken(null)
    setProfile(null)
    queryClient.removeQueries({ queryKey: ['player'] })
    if (current) {
      try {
        await api.players.disconnect(current)
      } catch (error) {
        if (!(error instanceof ApiError && error.status === 401)) throw error
      }
    }
  }, [token, queryClient])

  const refresh = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: ['player'] })
  }, [queryClient])

  const value = useMemo<PlayerContextValue>(() => {
    const resolvedProfile = profile ?? profileQuery.data ?? null
    const connected = token !== null && resolvedProfile !== null

    return {
      token,
      profile: resolvedProfile,
      status: token === null ? 'signed-out' : connected ? 'connected' : 'connecting',
      connect,
      disconnect,
      refresh,
    }
  }, [token, profile, profileQuery.data, connect, disconnect, refresh])

  return <PlayerContext.Provider value={value}>{children}</PlayerContext.Provider>
}

export function usePlayer(): PlayerContextValue {
  const context = useContext(PlayerContext)
  if (!context) throw new Error('usePlayer must be used inside <PlayerProvider>.')
  return context
}
