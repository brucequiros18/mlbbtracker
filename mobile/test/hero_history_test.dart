import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mlbb_tracker/features/heroes/domain/hero.dart';
import 'package:mlbb_tracker/features/heroes/domain/hero_repository.dart';
import 'package:mlbb_tracker/features/heroes/presentation/hero_detail_screen.dart';
import 'package:mlbb_tracker/features/heroes/presentation/hero_providers.dart';
import 'package:mlbb_tracker/shared/local/local_store.dart';
import 'package:shared_preferences/shared_preferences.dart';

class _FakeHeroRepository implements HeroRepository {
  _FakeHeroRepository({this.history = const []});

  final List<HeroHistoryPoint> history;

  @override
  Future<List<HeroSummary>> listHeroes({String? role, String? lane}) async => const [
        HeroSummary(id: 88, name: 'Masha', slug: 'masha', roles: ['Fighter'], lanes: ['Exp']),
      ];

  @override
  Future<HeroDetail> getHero(String identifier) async =>
      const HeroDetail(id: 88, name: 'Masha', slug: 'masha', roles: ['Fighter'], lanes: ['Exp']);

  @override
  Future<List<HeroRankStat>> heroRankings({
    int days = 7,
    String rank = 'all',
    String sortField = 'win_rate',
  }) async =>
      const [HeroRankStat(id: 88, name: 'Masha', winRate: 0.61, banRate: 0.43, pickRate: 0.005)];

  @override
  Future<List<HeroTrendPoint>> heroTrends(String identifier, {int days = 7}) async =>
      const [
        HeroTrendPoint(date: '2026-11-10', winRate: 0.54, banRate: 0.02, pickRate: 0.003),
        HeroTrendPoint(date: '2026-11-11', winRate: 0.55, banRate: 0.02, pickRate: 0.003),
      ];

  @override
  Future<List<HeroHistoryPoint>> heroHistory(String identifier) async => history;
}

Widget _app(HeroRepository repo, LocalStore store) => ProviderScope(
      overrides: [
        localStoreProvider.overrideWithValue(store),
        heroRepositoryProvider.overrideWithValue(repo),
      ],
      child: const MaterialApp(home: HeroDetailScreen(identifier: '88')),
    );

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  testWidgets('recorded history renders as a separate "Our Observations" section',
      (tester) async {
    final prefs = await SharedPreferences.getInstance();
    final repo = _FakeHeroRepository(
      history: const [
        HeroHistoryPoint(
          capturedOn: '2026-11-13',
          winRate: 0.58,
          banRate: 0.2,
          pickRate: 0.01,
          rankPosition: 4,
        ),
        HeroHistoryPoint(
          capturedOn: '2026-11-14',
          winRate: 0.6,
          banRate: 0.21,
          pickRate: 0.011,
          rankPosition: 3,
        ),
      ],
    );

    await tester.pumpWidget(_app(repo, LocalStore(prefs)));
    await tester.pumpAndSettle();

    // The provider trend and our own observations are labelled separately.
    expect(find.text('Win Rate Trend'), findsOneWidget);
    expect(find.text('Our Observations'), findsOneWidget);
    expect(find.text('Daily snapshots recorded by this backend'), findsOneWidget);
    expect(find.textContaining('2 daily snapshots recorded'), findsOneWidget);
  });

  testWidgets('recorded history shows an honest empty state before any snapshot',
      (tester) async {
    final prefs = await SharedPreferences.getInstance();

    await tester.pumpWidget(_app(_FakeHeroRepository(), LocalStore(prefs)));
    await tester.pumpAndSettle();

    expect(find.text('Our Observations'), findsOneWidget);
    expect(
      find.textContaining('No snapshots recorded yet'),
      findsOneWidget,
    );
  });

  testWidgets('a single snapshot is reported, not drawn as a trend line', (tester) async {
    final prefs = await SharedPreferences.getInstance();
    final repo = _FakeHeroRepository(
      history: const [
        HeroHistoryPoint(
          capturedOn: '2026-11-14',
          winRate: 0.6,
          banRate: 0.21,
          pickRate: 0.011,
        ),
      ],
    );

    await tester.pumpWidget(_app(repo, LocalStore(prefs)));
    await tester.pumpAndSettle();

    expect(find.textContaining('One snapshot recorded on 11-14'), findsOneWidget);
    expect(find.textContaining('A line appears after the next daily capture'), findsOneWidget);
  });
}
