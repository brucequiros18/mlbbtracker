import 'package:flutter/foundation.dart';

/// A player's profile.
///
/// Populated only through the **consented connect flow**: the player signs in
/// as themselves with a one-time code delivered in-game. Anonymous lookups are
/// not supported by any permitted public source.
@immutable
class PlayerProfile {
  const PlayerProfile({
    required this.playerId,
    required this.zoneId,
    required this.ign,
    this.avatar,
    this.level,
    this.rankLevel,
    this.rankName,
    this.rankIcon,
    this.totalMatches,
    this.wins,
    this.losses,
    this.winRate,
    this.kda,
    this.mvpCount,
  });

  final String playerId;
  final String zoneId;
  final String ign;
  final String? avatar;
  final int? level;
  final int? rankLevel;
  final String? rankName;
  final String? rankIcon;
  final int? totalMatches;
  final int? wins;
  final int? losses;
  final double? winRate;
  final double? kda;
  final int? mvpCount;

  factory PlayerProfile.fromJson(Map<String, dynamic> json) => PlayerProfile(
        playerId: json['playerId'].toString(),
        zoneId: json['zoneId'].toString(),
        ign: json['ign'] as String? ?? 'Unknown',
        avatar: json['avatar'] as String?,
        level: (json['level'] as num?)?.toInt(),
        rankLevel: (json['rankLevel'] as num?)?.toInt(),
        rankName: json['rankName'] as String?,
        rankIcon: json['rankIcon'] as String?,
        totalMatches: (json['totalMatches'] as num?)?.toInt(),
        wins: (json['wins'] as num?)?.toInt(),
        losses: (json['losses'] as num?)?.toInt(),
        winRate: (json['winRate'] as num?)?.toDouble(),
        kda: (json['kda'] as num?)?.toDouble(),
        mvpCount: (json['mvpCount'] as num?)?.toInt(),
      );
}

/// Aggregate statistics for the connected player (provider field semantics).
@immutable
class PlayerStats {
  const PlayerStats({
    this.totalMatches,
    this.wins,
    this.winRate,
    this.avgScore,
    this.playtimeHours,
    this.mvpCount,
    this.winStreak,
  });

  final int? totalMatches;
  final int? wins;
  final double? winRate;
  final double? avgScore;
  final double? playtimeHours;
  final int? mvpCount;
  final int? winStreak;

  factory PlayerStats.fromJson(Map<String, dynamic> json) => PlayerStats(
        totalMatches: (json['totalMatches'] as num?)?.toInt(),
        wins: (json['wins'] as num?)?.toInt(),
        winRate: (json['winRate'] as num?)?.toDouble(),
        avgScore: (json['avgScore'] as num?)?.toDouble(),
        playtimeHours: (json['playtimeHours'] as num?)?.toDouble(),
        mvpCount: (json['mvpCount'] as num?)?.toInt(),
        winStreak: (json['winStreak'] as num?)?.toInt(),
      );
}

/// One match from the player's history. KDA is derived from real K/D/A.
@immutable
class PlayerMatch {
  const PlayerMatch({
    this.battleId,
    this.seasonId,
    this.heroId,
    this.heroName,
    this.heroIcon,
    required this.kills,
    required this.deaths,
    required this.assists,
    required this.kda,
    required this.mvp,
    required this.won,
    this.score,
    this.laneId,
    required this.playedAt,
  });

  final String? battleId;
  final int? seasonId;
  final int? heroId;
  final String? heroName;
  final String? heroIcon;
  final int kills;
  final int deaths;
  final int assists;
  final double kda;
  final bool mvp;
  final bool won;
  final int? score;
  final int? laneId;
  final DateTime? playedAt;

  factory PlayerMatch.fromJson(Map<String, dynamic> json) => PlayerMatch(
        battleId: json['battleId']?.toString(),
        seasonId: (json['seasonId'] as num?)?.toInt(),
        heroId: (json['heroId'] as num?)?.toInt(),
        heroName: json['heroName'] as String?,
        heroIcon: json['heroIcon'] as String?,
        kills: (json['kills'] as num?)?.toInt() ?? 0,
        deaths: (json['deaths'] as num?)?.toInt() ?? 0,
        assists: (json['assists'] as num?)?.toInt() ?? 0,
        kda: (json['kda'] as num?)?.toDouble() ?? 0,
        mvp: json['mvp'] == true,
        won: json['won'] == true,
        score: (json['score'] as num?)?.toInt(),
        laneId: (json['laneId'] as num?)?.toInt(),
        playedAt: DateTime.tryParse(json['playedAt'] as String? ?? ''),
      );
}

@immutable
class PlayerMatchesPage {
  const PlayerMatchesPage({
    required this.matches,
    this.nextCursor,
    this.hasNext = false,
  });

  final List<PlayerMatch> matches;
  final String? nextCursor;
  final bool hasNext;

  factory PlayerMatchesPage.fromJson(Map<String, dynamic> json) => PlayerMatchesPage(
        matches: ((json['data'] as List?) ?? const [])
            .map((e) => PlayerMatch.fromJson(e as Map<String, dynamic>))
            .toList(growable: false),
        nextCursor: json['nextCursor'] as String?,
        hasNext: json['hasNext'] == true,
      );
}

@immutable
class FrequentHero {
  const FrequentHero({
    this.heroId,
    this.heroName,
    this.heroIcon,
    this.totalMatches,
    this.wins,
    this.winRate,
  });

  final int? heroId;
  final String? heroName;
  final String? heroIcon;
  final int? totalMatches;
  final int? wins;
  final double? winRate;

  factory FrequentHero.fromJson(Map<String, dynamic> json) => FrequentHero(
        heroId: (json['heroId'] as num?)?.toInt(),
        heroName: json['heroName'] as String?,
        heroIcon: json['heroIcon'] as String?,
        totalMatches: (json['totalMatches'] as num?)?.toInt(),
        wins: (json['wins'] as num?)?.toInt(),
        winRate: (json['winRate'] as num?)?.toDouble(),
      );
}

/// Result of a successful connect: the opaque backend session + profile.
@immutable
class ConnectResult {
  const ConnectResult({required this.sessionToken, required this.player});

  final String sessionToken;
  final PlayerProfile player;
}

/// A recent player search persisted on-device.
@immutable
class RecentSearch {
  const RecentSearch({required this.playerId, required this.zoneId, required this.searchedAt});

  final String playerId;
  final String zoneId;
  final DateTime searchedAt;

  Map<String, dynamic> toJson() => {
        'playerId': playerId,
        'zoneId': zoneId,
        'searchedAt': searchedAt.toIso8601String(),
      };

  factory RecentSearch.fromJson(Map<String, dynamic> json) => RecentSearch(
        playerId: json['playerId'] as String,
        zoneId: json['zoneId'] as String,
        searchedAt: DateTime.tryParse(json['searchedAt'] as String? ?? '') ?? DateTime.now(),
      );

  String get label => '$playerId ($zoneId)';
}
