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

const _pendingAccount = Account(
  id: 1,
  email: 'ash@example.com',
  googleName: 'Ash',
  profileComplete: false,
  mlbbIdVerified: false,
);

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
    required FakeAuthRepository authRepo,
    FakePlayerRepository? playerRepo,
  }) async {
    // A tall viewport so lazily built list children (the form's submit button)
    // are laid out without scrolling.
    tester.view.physicalSize = const Size(1400, 2600);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);
    final prefs = await SharedPreferences.getInstance();
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          localStoreProvider.overrideWithValue(LocalStore(prefs)),
          authRepositoryProvider.overrideWithValue(authRepo),
          playerRepositoryProvider.overrideWithValue(
            playerRepo ?? FakePlayerRepository(),
          ),
        ],
        child: const MaterialApp(home: PlayerSearchScreen()),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets('signed out: explains Google is the only sign-in', (tester) async {
    await pumpPlayers(tester, authRepo: FakeAuthRepository());

    expect(find.text('Sign in'), findsOneWidget);
    expect(find.textContaining('accounts are created with Google'), findsOneWidget);
    // No client ID on this server: say so instead of offering a dead button.
    expect(find.text('Google sign-in is not configured'), findsOneWidget);
    expect(find.textContaining('Nothing is faked'), findsOneWidget);
  });

  testWidgets('first Google sign-in asks for the profile', (tester) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('account_session_token', 'account-token');

    await pumpPlayers(
      tester,
      authRepo: FakeAuthRepository(account: _pendingAccount),
    );

    expect(find.text('Finish your account'), findsOneWidget);
    expect(find.text('Signed in as ash@example.com'), findsOneWidget);
    expect(find.textContaining('self-declared'), findsWidgets);
  });

  testWidgets('completing the profile unlocks the connect step', (tester) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('account_session_token', 'account-token');
    final authRepo = FakeAuthRepository(account: _pendingAccount);

    await pumpPlayers(tester, authRepo: authRepo);

    await tester.enterText(find.byType(TextField).at(0), 'AshKetchum');
    await tester.enterText(find.byType(TextField).at(1), '123456789');
    await tester.enterText(find.byType(TextField).at(2), 'correct horse battery');
    await tester.enterText(find.byType(TextField).at(3), 'correct horse battery');
    await tester.tap(find.text('Create my profile'));
    await tester.pumpAndSettle();

    expect(authRepo.registered, [
      {'username': 'AshKetchum', 'mlbbId': '123456789'},
    ]);
    expect(find.text('Connect your game account'), findsOneWidget);
  });

  testWidgets('rejects a mismatched password before calling the server', (tester) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('account_session_token', 'account-token');
    final authRepo = FakeAuthRepository(account: _pendingAccount);

    await pumpPlayers(tester, authRepo: authRepo);

    await tester.enterText(find.byType(TextField).at(0), 'AshKetchum');
    await tester.enterText(find.byType(TextField).at(1), '123456789');
    await tester.enterText(find.byType(TextField).at(2), 'correct horse battery');
    await tester.enterText(find.byType(TextField).at(3), 'different password');
    await tester.tap(find.text('Create my profile'));
    await tester.pumpAndSettle();

    expect(authRepo.registered, isEmpty);
    expect(find.text('Passwords do not match'), findsOneWidget);
  });

  testWidgets('the MLBB ID is labelled self-declared, not verified', (tester) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('account_session_token', 'account-token');

    await pumpPlayers(
      tester,
      authRepo: FakeAuthRepository(account: _completeAccount),
    );

    expect(find.text('AshKetchum'), findsOneWidget);
    expect(find.text('MLBB ID 123456789'), findsOneWidget);
    expect(find.text('self-declared'), findsOneWidget);
  });

  testWidgets('signing out clears the account and the game link', (tester) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('account_session_token', 'account-token');
    await prefs.setString('player_session_token', 'session-abc');
    final authRepo = FakeAuthRepository(account: _completeAccount);

    await pumpPlayers(tester, authRepo: authRepo);

    await tester.tap(find.byTooltip('Sign out'));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(FilledButton, 'Sign out'));
    await tester.pumpAndSettle();

    expect(authRepo.signOutCalls, 1);
    expect(prefs.getString('account_session_token'), isNull);
    expect(prefs.getString('player_session_token'), isNull);
    expect(find.text('Google sign-in is not configured'), findsOneWidget);
  });
}
