import 'hero.dart';

/// Read-only access to hero data. Implemented against the MLBB Tracker
/// backend; overridden in tests with an in-memory fake.
abstract interface class HeroRepository {
  Future<List<HeroSummary>> listHeroes({String? role, String? lane});

  Future<HeroDetail> getHero(String identifier);

  /// Hero win/ban/pick rates, sorted, for the given window and rank.
  Future<List<HeroRankStat>> heroRankings({
    int days,
    String rank,
    String sortField,
  });

  /// Daily win/ban/pick timeline for one hero, ascending by date.
  Future<List<HeroTrendPoint>> heroTrends(String identifier, {int days});
}
