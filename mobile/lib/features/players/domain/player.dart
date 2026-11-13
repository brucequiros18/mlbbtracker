import 'package:flutter/foundation.dart';

/// A player's public profile.
///
/// NOTE: as of the Milestone 1 API research, no legitimate public source
/// exposes per-player statistics (see docs/API_DOCUMENTATION.md). This model
/// exists so the app is ready if a permitted source appears; the backend
/// currently answers player lookups with a clear "unsupported" response.
@immutable
class PlayerProfile {
  const PlayerProfile({
    required this.playerId,
    required this.zoneId,
    required this.ign,
    this.avatar,
    this.level,
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
