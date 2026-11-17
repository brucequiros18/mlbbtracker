import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mlbb_tracker/features/auth/domain/account.dart';
import 'package:mlbb_tracker/features/auth/presentation/auth_providers.dart';
import 'package:mlbb_tracker/features/players/presentation/player_providers.dart';
import 'package:mlbb_tracker/features/players/presentation/player_search_screen.dart';
import 'package:mlbb_tracker/shared/local/local_store.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'fakes.dart';

const _completeAccount = Account(
  id: 1,
  email: 'ash@example.com',
  googleName: 'Ash',
  username: 'AshKetchum',
  mlbbId: '123456789',
  profileComplete: true,
  mlbbIdVerified: false,
);

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  Future<void> pumpPlayers(
    WidgetTester tester, {
    required FakePlayerRepository playerRepo,
    required FakeAuthRepository authRepo,
  }) async {
    tester.view.physicalSize = const Size(1400, 2600);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);
    final prefs = await SharedPreferences.getInstance();
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          localStoreProvider.overrideWithValue(LocalStore(prefs)),
          playerRepositoryProvider.overrideWithValue(playerRepo),
          authRepositoryProvider.overrideWithValue(authRepo),
        ],
        child: const MaterialApp(home: PlayerSearchScreen()),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets('connect view explains the consented in-game sign-in', (tester) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('account_session_token', 'account-token');
    final playerRepo = FakePlayerRepository();

    await pumpPlayers(
      tester,
      playerRepo: playerRepo,
      authRepo: FakeAuthRepository(account: _completeAccount),
    );

    expect(find.text('Connect your game account'), findsOneWidget);
    expect(find.textContaining('We never ask for your Moonton password'), findsOneWidget);

    // Sending a code reveals the verification step.
    await tester.enterText(find.byType(TextField).at(0), '123456789');
    await tester.enterText(find.byType(TextField).at(1), '1234');
    await tester.tap(find.text('Send verification code'));
    await tester.pumpAndSettle();

    expect(playerRepo.startCalls, 1);
    expect(find.text('Verification code'), findsOneWidget);
  });

  testWidgets('connected dashboard renders real stats and matches', (tester) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('account_session_token', 'account-token');
    await prefs.setString('player_session_token', 'session-abc');

    await pumpPlayers(
      tester,
      playerRepo: FakePlayerRepository(),
      authRepo: FakeAuthRepository(account: _completeAccount),
    );

    expect(find.text('TestPlayer'), findsOneWidget);
    expect(find.text('60.0%'), findsOneWidget);
    expect(find.text('Masha'), findsWidgets);
    expect(find.text('WIN'), findsOneWidget);
    // The app account stays visible above the connected statistics.
    expect(find.text('AshKetchum'), findsOneWidget);
  });
}
