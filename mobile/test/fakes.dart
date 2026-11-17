import 'package:mlbb_tracker/core/network/api_exception.dart';
import 'package:mlbb_tracker/features/auth/domain/account.dart';
import 'package:mlbb_tracker/features/auth/domain/auth_repository.dart';
import 'package:mlbb_tracker/features/players/domain/player.dart';
import 'package:mlbb_tracker/features/players/domain/player_repository.dart';

/// In-memory account backend for widget tests.
class FakeAuthRepository implements AuthRepository {
  FakeAuthRepository({
    this.account,
    this.authConfig = const AuthConfig(googleSignInEnabled: false),
  });

  Account? account;
  AuthConfig authConfig;

  final registered = <Map<String, String>>[];
  int signOutCalls = 0;

  @override
  Future<AuthConfig> config() async => authConfig;

  @override
  Future<AuthSessionResult> signInWithGoogle(String credential) async {
    account ??= const Account(
      id: 1,
      email: 'ash@example.com',
      googleName: 'Ash',
      profileComplete: false,
      mlbbIdVerified: false,
    );
    return AuthSessionResult(
      sessionToken: 'account-token',
      account: account!,
      isNewUser: true,
    );
  }

  @override
  Future<Account> register({
    required String token,
    required String username,
    required String mlbbId,
    required String password,
  }) async {
    registered.add({'username': username, 'mlbbId': mlbbId});
    final current = account;
    if (current == null) {
      throw ApiException(ApiErrorKind.unauthorized, 'Sign in first.');
    }
    account = Account(
      id: current.id,
      email: current.email,
      googleName: current.googleName,
      pictureUrl: current.pictureUrl,
      username: username,
      mlbbId: mlbbId,
      profileComplete: true,
      mlbbIdVerified: false,
    );
    return account!;
  }

  @override
  Future<Account> me(String token) async {
    final current = account;
    if (current == null) {
      throw ApiException(ApiErrorKind.unauthorized, 'Not signed in.');
    }
    return current;
  }

  @override
  Future<Account> updateProfile({
    required String token,
    String? username,
    String? mlbbId,
    required String currentPassword,
    String? newPassword,
  }) async {
    final current = account;
    if (current == null) {
      throw ApiException(ApiErrorKind.unauthorized, 'Not signed in.');
    }
    account = Account(
      id: current.id,
      email: current.email,
      googleName: current.googleName,
      pictureUrl: current.pictureUrl,
      username: username ?? current.username,
      mlbbId: mlbbId ?? current.mlbbId,
      profileComplete: current.profileComplete,
      mlbbIdVerified: false,
    );
    return account!;
  }

  @override
  Future<void> logout(String token) async {
    signOutCalls++;
  }
}

/// Player statistics backend for widget tests (consented connect flow).
class FakePlayerRepository implements PlayerRepository {
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
