/** Wire types for the Laravel `/api/v1` contract. */

export interface ApiMeta {
  generatedAt: string
  cached: boolean
  count: number | null
  note: string | null
  sources: ApiSource[]
}

export interface ApiSource {
  name: string
  url: string
  license: string | null
}

export interface ApiEnvelope<T> {
  data: T
  meta: ApiMeta
}

export interface HeroSummary {
  id: number
  name: string
  slug: string
  roles: string[]
  lanes: string[]
  headImage: string | null
  tier: string | null
}

export interface HeroRanking {
  id: number
  name: string
  slug: string
  headImage: string | null
  winRate: number
  banRate: number
  pickRate: number
  tier: string | null
}

export interface HeroSkill {
  name: string
  description: string
}

export interface HeroRankStat {
  winRate: number
  banRate: number
  pickRate: number
}

export interface HeroDetail {
  id: number
  name: string
  slug: string
  roles: string[]
  lanes: string[]
  specialties: string[]
  headImage: string | null
  portrait: string | null
  skills: HeroSkill[]
  strongAgainst: string[]
  weakAgainst: string[]
  rankStat: HeroRankStat | null
}

export interface TrendPoint {
  date: string
  winRate: number
  banRate: number
  pickRate: number
}

export interface HistoryPoint {
  capturedOn: string
  winRate: number
  banRate: number
  pickRate: number
  tier: string | null
  rankPosition: number | null
}

export interface Standing {
  rank: number
  teamCode: string
  teamName: string
  logo: string | null
  matchPoint: number
  matchWins: number
  matchLosses: number
  netGameWin: number
  gameWins: number
  gameLosses: number
}

export interface Account {
  id: number
  email: string
  googleName: string | null
  pictureUrl: string | null
  username: string | null
  mlbbId: string | null
  profileComplete: boolean
  /** The MLBB ID is self-declared - it is never checked against Moonton. */
  mlbbIdVerified: false
  createdAt: string | null
  lastLoginAt: string | null
}

export interface AuthConfig {
  googleSignInEnabled: boolean
  googleClientId: string | null
  minPasswordLength: number
  maxPasswordLength: number
  usernamePattern: string
  mlbbIdPattern: string
}

export interface GoogleSignInResult {
  sessionToken: string
  user: Account
  isNewUser: boolean
}

export interface PlayerProfile {
  playerId: string
  zoneId: string
  ign: string
  avatar: string | null
  level: number | null
  rankLevel: number | null
  rankName: string | null
  rankIcon: string | null
  totalMatches: number | null
  wins: number | null
  losses: number | null
  winRate: number | null
  kda: number | null
  mvpCount: number | null
}

export interface PlayerStats {
  totalMatches: number | null
  wins: number | null
  winRate: number | null
  avgScore: number | null
  playtimeHours: number | null
  mvpCount: number | null
  winStreak: number | null
}

export interface PlayerMatch {
  battleId: string | null
  seasonId: number | null
  heroId: number | null
  heroName: string | null
  heroIcon: string | null
  kills: number
  deaths: number
  assists: number
  kda: number
  mvp: boolean
  won: boolean
  score: number | null
  laneId: number | null
  playedAt: string
}

export interface PlayerMatchesPage {
  data: PlayerMatch[]
  nextCursor: string | null
  hasNext: boolean
}

export interface FrequentHero {
  heroId: number | null
  heroName: string | null
  heroIcon: string | null
  totalMatches: number | null
  wins: number | null
  winRate: number | null
}

export interface HealthPayload {
  status: string
  app: string
  environment: string
  cache: { store: string; entries: number | null }
  providers: Record<string, string | null>
  capabilities: Record<string, boolean>
}

export type RankWindow = '1' | '3' | '7' | '15' | '30'
export type RankTier = 'all' | 'epic' | 'legend' | 'mythic' | 'honor' | 'glory'
export type SortField = 'win_rate' | 'ban_rate' | 'pick_rate'
export type League = 'id' | 'ph' | 'my' | 'kh'
