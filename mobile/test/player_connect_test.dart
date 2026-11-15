import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mlbb_tracker/features/players/domain/player.dart';
import 'package:mlbb_tracker/features/players/domain/player_repository.dart';
import 'package:mlbb_tracker/features/players/presentation/player_providers.dart';
import 'package:mlbb_tracker/features/players/presentation/player_search_screen.dart';
import 'package:mlbb_tracker/shared/local/local_store.dart';
import 'package:shared_preferences/shared_preferences.dart';

class _FakePlayerRepository implements PlayerRepository {
  int startCalls = 0;
  int verifyCalls = 0;

  @override
  Future<PlayerProfile> lookup({required String playerId, required String zoneId}) async =>
      throw UnimplementedError();

  @override
  Future<void> connectStart({required String playerId, required String zoneId}) async {
    startCalls++;
  }

  @override
  Future<ConnectResult> connectVerify({
    required String playerId,
    required String zoneId,
    required String code,
  }) async =>
      ConnectResult(
        sessionToken: 'session-abc',
        player: PlayerProfile(playerId: playerId, zoneId: zoneId, ign: 'TestPlayer'),
      );

  @override
  Future<void> disconnect(String sessionToken) async {}

  @override
  Future<PlayerProfile> profile(String sessionToken) async =>
      const PlayerProfile(playerId: '123456789', zoneId: '1234', ign: 'TestPlayer', level: 42);

  @override
  Future<PlayerStats> stats(String sessionToken) async =>
      const PlayerStats(totalMatches: 100, wins: 60, winRate: 0.6, mvpCount: 14, winStreak: 7);

  @override
  Future<PlayerMatchesPage> matches(String sessionToken, {int limit = 20, String? cursor}) async =>
      const PlayerMatchesPage(
        matches: [
          PlayerMatch(
            heroName: 'Masha',
            kills: 8,
            deaths: 2,
            assists: 5,
            kda: 6.5,
            mvp: true,
            won: true,
            playedAt: null,
          ),
        ],
      );

  @override
  Future<List<FrequentHero>> frequentHeroes(String sessionToken, {int limit = 10}) async =>
      const [FrequentHero(heroName: 'Masha', totalMatches: 40, winRate: 0.65)];
}

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  testWidgets('connect view explains the consented sign-in flow', (tester) async {
    final prefs = await SharedPreferences.getInstance();
    final repo = _FakePlayerRepository();

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          localStoreProvider.overrideWithValue(LocalStore(prefs)),
          playerRepositoryProvider.overrideWithValue(repo),
        ],
        child: const MaterialApp(home: PlayerSearchScreen()),
      ),
    );

    expect(find.text('Connect your account'), findsOneWidget);
    expect(find.text('No password is ever requested. Your account token is stored on the '
        'backend, never in the app.'), findsOneWidget);

    // Sending a code reveals the verification step.
    await tester.enterText(find.byType(TextField).at(0), '123456789');
    await tester.enterText(find.byType(TextField).at(1), '1234');
    await tester.tap(find.text('Send verification code'));
    await tester.pumpAndSettle();

    expect(repo.startCalls, 1);
    expect(find.text('Verification code'), findsOneWidget);
  });

  testWidgets('connected dashboard renders real stats and matches', (tester) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('player_session_token', 'session-abc');

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          localStoreProvider.overrideWithValue(LocalStore(prefs)),
          playerRepositoryProvider.overrideWithValue(_FakePlayerRepository()),
        ],
        child: const MaterialApp(home: PlayerSearchScreen()),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('TestPlayer'), findsOneWidget);
    expect(find.text('60.0%'), findsOneWidget);
    expect(find.text('Masha'), findsWidgets);
    expect(find.text('WIN'), findsOneWidget);
  });
}
