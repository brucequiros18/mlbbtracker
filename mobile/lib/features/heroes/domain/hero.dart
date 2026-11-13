import 'package:flutter/foundation.dart';

/// Summary of a hero as returned by the MLBB Tracker backend.
@immutable
class HeroSummary {
  const HeroSummary({
    required this.id,
    required this.name,
    required this.slug,
    required this.roles,
    required this.lanes,
    this.headImage,
    this.tier,
  });

  final int id;
  final String name;
  final String slug;
  final List<String> roles;
  final List<String> lanes;
  final String? headImage;
  final String? tier;

  factory HeroSummary.fromJson(Map<String, dynamic> json) => HeroSummary(
        id: (json['id'] as num).toInt(),
        name: json['name'] as String,
        slug: json['slug'] as String? ?? '',
        roles: (json['roles'] as List?)?.map((e) => e.toString()).toList() ?? const [],
        lanes: (json['lanes'] as List?)?.map((e) => e.toString()).toList() ?? const [],
        headImage: json['headImage'] as String?,
        tier: json['tier'] as String?,
      );

  String get primaryRole => roles.isNotEmpty ? roles.first : 'Unknown';
}

/// A hero's competitive statistics for a rank window.
@immutable
class HeroRankStat {
  const HeroRankStat({
    required this.id,
    required this.name,
    required this.winRate,
    required this.banRate,
    required this.pickRate,
    this.headImage,
    this.tier,
  });

  final int id;
  final String name;
  final double winRate;
  final double banRate;
  final double pickRate;
  final String? headImage;
  final String? tier;

  factory HeroRankStat.fromJson(Map<String, dynamic> json) => HeroRankStat(
        id: (json['id'] as num).toInt(),
        name: json['name'] as String,
        winRate: (json['winRate'] as num?)?.toDouble() ?? 0,
        banRate: (json['banRate'] as num?)?.toDouble() ?? 0,
        pickRate: (json['pickRate'] as num?)?.toDouble() ?? 0,
        headImage: json['headImage'] as String?,
        tier: json['tier'] as String?,
      );
}

@immutable
class HeroSkill {
  const HeroSkill({required this.name, required this.description, this.icon});

  final String name;
  final String description;
  final String? icon;

  factory HeroSkill.fromJson(Map<String, dynamic> json) => HeroSkill(
        name: json['name'] as String? ?? '',
        description: json['description'] as String? ?? '',
        icon: json['icon'] as String?,
      );
}

/// Full hero profile including skills and relationship lists.
@immutable
class HeroDetail {
  const HeroDetail({
    required this.id,
    required this.name,
    required this.slug,
    required this.roles,
    required this.lanes,
    this.headImage,
    this.portrait,
    this.skills = const [],
    this.strongAgainst = const [],
    this.weakAgainst = const [],
    this.rankStat,
  });

  final int id;
  final String name;
  final String slug;
  final List<String> roles;
  final List<String> lanes;
  final String? headImage;
  final String? portrait;
  final List<HeroSkill> skills;
  final List<String> strongAgainst;
  final List<String> weakAgainst;
  final HeroRankStat? rankStat;

  factory HeroDetail.fromJson(Map<String, dynamic> json) => HeroDetail(
        id: (json['id'] as num).toInt(),
        name: json['name'] as String,
        slug: json['slug'] as String? ?? '',
        roles: (json['roles'] as List?)?.map((e) => e.toString()).toList() ?? const [],
        lanes: (json['lanes'] as List?)?.map((e) => e.toString()).toList() ?? const [],
        headImage: json['headImage'] as String?,
        portrait: json['portrait'] as String?,
        skills: (json['skills'] as List?)
                ?.map((e) => HeroSkill.fromJson(e as Map<String, dynamic>))
                .toList() ??
            const [],
        strongAgainst:
            (json['strongAgainst'] as List?)?.map((e) => e.toString()).toList() ?? const [],
        weakAgainst:
            (json['weakAgainst'] as List?)?.map((e) => e.toString()).toList() ?? const [],
        rankStat: json['rankStat'] == null
            ? null
            : HeroRankStat.fromJson(json['rankStat'] as Map<String, dynamic>),
      );
}
