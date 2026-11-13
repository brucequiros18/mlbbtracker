import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/dio_client.dart';
import '../data/hero_repository_impl.dart';
import '../domain/hero.dart';
import '../domain/hero_repository.dart';

/// Query key for a hero trend timeline (identifier + window).
@immutable
class TrendQuery {
  const TrendQuery(this.identifier, this.days);

  final String identifier;
  final int days;

  @override
  bool operator ==(Object other) =>
      other is TrendQuery && other.identifier == identifier && other.days == days;

  @override
  int get hashCode => Object.hash(identifier, days);
}

final heroRepositoryProvider = Provider<HeroRepository>(
  (ref) => HeroRepositoryImpl(ref.watch(dioProvider)),
);

/// Selected role filter on the Heroes tab ("All" = no filter).
final heroRoleFilterProvider = StateProvider<String>((ref) => 'All');

/// Hero list filtered by the active role filter.
final heroListProvider = FutureProvider.autoDispose<List<HeroSummary>>((ref) {
  final role = ref.watch(heroRoleFilterProvider);
  return ref.watch(heroRepositoryProvider).listHeroes(role: role);
});

/// Full, unfiltered hero roster (used to resolve saved hero ids).
final allHeroesProvider = FutureProvider<List<HeroSummary>>((ref) {
  return ref.watch(heroRepositoryProvider).listHeroes();
});

final heroDetailProvider =
    FutureProvider.autoDispose.family<HeroDetail, String>((ref, identifier) {
  return ref.watch(heroRepositoryProvider).getHero(identifier);
});

/// Hero ranking window in days (1/3/7/15/30).
final rankingDaysProvider = StateProvider<int>((ref) => 7);

/// Hero ranking sort field: win_rate | ban_rate | pick_rate.
final rankingSortProvider = StateProvider<String>((ref) => 'win_rate');

final heroTrendsProvider =
    FutureProvider.autoDispose.family<List<HeroTrendPoint>, TrendQuery>((ref, query) {
  return ref.watch(heroRepositoryProvider).heroTrends(query.identifier, days: query.days);
});

final heroRankingsProvider = FutureProvider.autoDispose<List<HeroRankStat>>((ref) {
  final days = ref.watch(rankingDaysProvider);
  final sort = ref.watch(rankingSortProvider);
  return ref.watch(heroRepositoryProvider).heroRankings(days: days, sortField: sort);
});
