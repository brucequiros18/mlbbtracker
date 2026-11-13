import 'package:flutter/foundation.dart';

/// A team's row in a professional league standings table.
@immutable
class EsportsStanding {
  const EsportsStanding({
    required this.rank,
    required this.teamCode,
    required this.teamName,
    this.logo,
    required this.matchPoint,
    required this.matchWins,
    required this.matchLosses,
    required this.netGameWin,
    required this.gameWins,
    required this.gameLosses,
  });

  final int rank;
  final String teamCode;
  final String teamName;
  final String? logo;
  final int matchPoint;
  final int matchWins;
  final int matchLosses;
  final int netGameWin;
  final int gameWins;
  final int gameLosses;

  factory EsportsStanding.fromJson(Map<String, dynamic> json) => EsportsStanding(
        rank: (json['rank'] as num?)?.toInt() ?? 0,
        teamCode: json['teamCode'] as String? ?? '',
        teamName: json['teamName'] as String? ?? '',
        logo: json['logo'] as String?,
        matchPoint: (json['matchPoint'] as num?)?.toInt() ?? 0,
        matchWins: (json['matchWins'] as num?)?.toInt() ?? 0,
        matchLosses: (json['matchLosses'] as num?)?.toInt() ?? 0,
        netGameWin: (json['netGameWin'] as num?)?.toInt() ?? 0,
        gameWins: (json['gameWins'] as num?)?.toInt() ?? 0,
        gameLosses: (json['gameLosses'] as num?)?.toInt() ?? 0,
      );
}
