import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mlbb_tracker/features/heroes/domain/hero.dart';
import 'package:mlbb_tracker/features/heroes/domain/hero_repository.dart';
import 'package:mlbb_tracker/features/heroes/presentation/hero_providers.dart';
import 'package:mlbb_tracker/features/heroes/presentation/heroes_screen.dart';
import 'package:mlbb_tracker/shared/local/local_store.dart';
import 'package:shared_preferences/shared_preferences.dart';

class _FakeHeroRepository implements HeroRepository {
  @override
  Future<List<HeroSummary>> listHeroes({String? role, String? lane}) async => const [
        HeroSummary(id: 1, name: 'Khufra', slug: 'khufra', roles: ['Tank'], lanes: ['Roam']),
        HeroSummary(id: 2, name: 'Masha', slug: 'masha', roles: ['Fighter'], lanes: ['Exp']),
      ];

  @override
  Future<HeroDetail> getHero(String identifier) async =>
      const HeroDetail(id: 1, name: 'Khufra', slug: 'khufra', roles: ['Tank'], lanes: ['Roam']);

  @override
  Future<List<HeroRankStat>> heroRankings({
    int days = 7,
    String rank = 'all',
    String sortField = 'win_rate',
  }) async =>
      const [HeroRankStat(id: 1, name: 'Masha', winRate: 0.61, banRate: 0.42, pickRate: 0.55)];
}

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  testWidgets('Heroes screen renders hero roster from the repository', (tester) async {
    final prefs = await SharedPreferences.getInstance();

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          localStoreProvider.overrideWithValue(LocalStore(prefs)),
          heroRepositoryProvider.overrideWithValue(_FakeHeroRepository()),
        ],
        child: const MaterialApp(home: HeroesScreen()),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Heroes'), findsOneWidget);
    expect(find.text('Khufra'), findsOneWidget);
    expect(find.text('Masha'), findsOneWidget);
  });
}
