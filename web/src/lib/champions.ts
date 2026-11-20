import type { League } from './types'

/**
 * Completed-season results for the tracked leagues, curated by hand.
 *
 * The standings endpoint only carries the regular-season table; these
 * playoff results were verified against tournament coverage (Moonton
 * announcements, Liquipedia, national esports press) on 2026-11-21. Every
 * entry links its source so the numbers can be re-checked - nothing here is
 * invented.
 */
export interface SeasonResult {
  season: string
  champion: string
  runnerUp: string
  /** Grand-final series score, from the champion's perspective. */
  score: string
  /** When the grand final was played, as precise as the sources allow. */
  concluded: string
  note?: string
  source: string
}

export const VERIFIED_ON = 'Nov 21, 2026'

/** The most recent completed season per league. */
export const SEASON_CHAMPIONS: Record<League, SeasonResult> = {
  id: {
    season: 'Season 18',
    champion: 'Bigetron by Vitality',
    runnerUp: 'Natus Vincere',
    score: '4–3',
    concluded: '2026',
    note: 'Back-to-back titles (S17 & S18) - a first in the org\'s history. Both finalists head to M8.',
    source: 'https://en.moonton.com/news/397.html',
  },
  ph: {
    season: 'Season 16',
    champion: 'Team Liquid PH',
    runnerUp: 'Aurora Gaming',
    score: '4–0',
    concluded: 'Oct 26, 2026',
    note: 'Back-to-back champions (S15 & S16) - a 4–0 sweep at the Cuneta Astrodome. Finals MVP: Jaypee.',
    source: 'https://www.gmanetwork.com/news/sports/othersports/963805/mpl-ph-season-16-team-liquid-vs-aurora-finals-october-26-2026/story/',
  },
  my: {
    season: 'Season 18',
    champion: 'Selangor Red Giants',
    runnerUp: 'Team Rey',
    score: '4–3',
    concluded: 'Nov 2026',
    note: 'A six-peat at Stadium Juara, Kuala Lumpur. Champions and runners-up both qualified for M8.',
    source: 'https://www.nst.com.my/sports/esports/2026/11/1568822/srg-reign-supreme-sixth-straight-mpl-malaysia-title',
  },
  kh: {
    season: 'Season 11',
    champion: 'Vigor Apex',
    runnerUp: 'Team Flash KH',
    score: '4–2',
    concluded: 'Nov 15, 2026',
    note: 'An undefeated run through the season, capped in the grand final.',
    source: 'https://lifenewsagency.com/vigor-apex-beat-flash-kh-mpl-cambodia-season-11-champions',
  },
}

/** Recent grand finals per league, newest last. */
export const SEASON_HISTORY: Record<League, SeasonResult[]> = {
  id: [
    {
      season: 'Season 16',
      champion: 'ONIC Esports',
      runnerUp: 'Alter Ego',
      score: '4–1',
      concluded: 'Nov 2025',
      source: 'https://escharts.com/tournaments/mobile-legends/mpl-indonesia-season-16',
    },
    {
      season: 'Season 17',
      champion: 'Bigetron by Vitality',
      runnerUp: 'ONIC Esports',
      score: '4–1',
      concluded: 'Jun 14, 2026',
      note: 'Bigetron\'s first MPL Indonesia title, dethroning the Sky Kings.',
      source: 'https://en.moonton.com/news/350.html',
    },
    SEASON_CHAMPIONS.id,
  ],
  ph: [
    {
      season: 'Season 15',
      champion: 'Team Liquid PH',
      runnerUp: 'Aurora Gaming',
      score: '4–2',
      concluded: '2025',
      note: 'The first of the back-to-back run.',
      source: 'https://escharts.com/news/mpl-philippines-season-16-viewership',
    },
    SEASON_CHAMPIONS.ph,
  ],
  my: [
    {
      season: 'Season 17',
      champion: 'Selangor Red Giants',
      runnerUp: 'Team Vamos',
      score: '4–0',
      concluded: 'Jun 7, 2026',
      note: 'Fifth consecutive title.',
      source: 'https://home.kitamen.my/wiki/tournaments/mpl-malaysia',
    },
    SEASON_CHAMPIONS.my,
  ],
  kh: [
    {
      season: 'Season 10',
      champion: 'PRO Esports',
      runnerUp: 'Galaxy Legends',
      score: '4–0',
      concluded: 'May 17, 2026',
      source: 'https://escharts.com/tournaments/mobile-legends/mpl-cambodia-season-10/schedule',
    },
    SEASON_CHAMPIONS.kh,
  ],
}

/** The world championship, shown above every league. */
export const WORLD_CHAMPION: SeasonResult & { event: string; venue: string } = {
  event: 'M7 World Championship',
  season: 'M7',
  champion: 'Aurora Gaming PH',
  runnerUp: 'Alter Ego',
  score: '4–0',
  concluded: 'Jan 25, 2026',
  venue: 'Jakarta, Indonesia',
  note: 'The Philippines\' sixth consecutive world title. Finals MVP: Dylan "Light" Catipon.',
  source: 'https://liquipedia.net/mobilelegends/M7_World_Championship',
}
