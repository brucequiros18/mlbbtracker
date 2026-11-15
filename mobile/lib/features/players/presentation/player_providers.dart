import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/network/dio_client.dart';
import '../../../shared/local/local_store.dart';
import '../data/player_repository_impl.dart';
import '../domain/player.dart';
import '../domain/player_repository.dart';

final playerRepositoryProvider = Provider<PlayerRepository>(
  (ref) => PlayerRepositoryImpl(ref.watch(dioProvider)),
);

// — Session token (opaque app key; provider JWT never reaches the device) ——
final sessionTokenProvider =
    StateNotifierProvider<SessionTokenNotifier, String?>(
  (ref) => SessionTokenNotifier(ref.watch(localStoreProvider)),
);

class SessionTokenNotifier extends StateNotifier<String?> {
  SessionTokenNotifier(this._store) : super(_store.readSessionToken());

  final LocalStore _store;

  Future<void> save(String token) async {
    await _store.saveSessionToken(token);
    state = token;
  }

  Future<void> clear() async {
    await _store.clearSessionToken();
    state = null;
  }
}

// — Connect flow state ———————————————————————————————————————
sealed class ConnectState {
  const ConnectState();
}

class ConnectIdle extends ConnectState {
  const ConnectIdle();
}

class ConnectSendingCode extends ConnectState {
  const ConnectSendingCode();
}

/// A code was delivered to the player's in-game mailbox.
class ConnectCodeSent extends ConnectState {
  const ConnectCodeSent(this.playerId, this.zoneId);
  final String playerId;
  final String zoneId;
}

class ConnectVerifying extends ConnectState {
  const ConnectVerifying();
}

class ConnectError extends ConnectState {
  const ConnectError(this.message);
  final String message;
}

class ConnectController extends StateNotifier<ConnectState> {
  ConnectController(this._repo, this._tokens) : super(const ConnectIdle());

  final PlayerRepository _repo;
  final SessionTokenNotifier _tokens;

  Future<void> sendCode(String playerId, String zoneId) async {
    state = const ConnectSendingCode();
    try {
      await _repo.connectStart(playerId: playerId, zoneId: zoneId);
      state = ConnectCodeSent(playerId, zoneId);
    } on ApiException catch (e) {
      state = ConnectError(e.message);
    } catch (_) {
      state = const ConnectError('Could not reach the server. Please try again.');
    }
  }

  Future<void> verify(String playerId, String zoneId, String code) async {
    state = const ConnectVerifying();
    try {
      final result = await _repo.connectVerify(
        playerId: playerId,
        zoneId: zoneId,
        code: code,
      );
      await _tokens.save(result.sessionToken);
      state = const ConnectIdle();
    } on ApiException catch (e) {
      state = ConnectError(e.message);
    } catch (_) {
      state = const ConnectError('Could not reach the server. Please try again.');
    }
  }

  Future<void> disconnect() async {
    final token = _tokens.state;
    if (token != null) {
      try {
        await _repo.disconnect(token);
      } on ApiException {
        // Local sign-out must succeed even if the server call fails.
      }
    }
    await _tokens.clear();
    state = const ConnectIdle();
  }
}

final connectControllerProvider =
    StateNotifierProvider.autoDispose<ConnectController, ConnectState>(
  (ref) => ConnectController(
    ref.watch(playerRepositoryProvider),
    ref.watch(sessionTokenProvider.notifier),
  ),
);

// — Connected dashboard data —————————————————————————————————
String _requireToken(String? token) {
  if (token == null) {
    throw ApiException(ApiErrorKind.unauthorized, 'Not connected.');
  }
  return token;
}

final connectedProfileProvider = FutureProvider.autoDispose<PlayerProfile>((ref) {
  final token = _requireToken(ref.watch(sessionTokenProvider));
  return ref.watch(playerRepositoryProvider).profile(token);
});

final playerStatsProvider = FutureProvider.autoDispose<PlayerStats>((ref) {
  final token = _requireToken(ref.watch(sessionTokenProvider));
  return ref.watch(playerRepositoryProvider).stats(token);
});

final playerMatchesProvider = FutureProvider.autoDispose<PlayerMatchesPage>((ref) {
  final token = _requireToken(ref.watch(sessionTokenProvider));
  return ref.watch(playerRepositoryProvider).matches(token);
});

final playerHeroesProvider = FutureProvider.autoDispose<List<FrequentHero>>((ref) {
  final token = _requireToken(ref.watch(sessionTokenProvider));
  return ref.watch(playerRepositoryProvider).frequentHeroes(token);
});

/// Recently searched players, persisted on-device.
final recentSearchesProvider =
    StateNotifierProvider<RecentSearchesNotifier, List<RecentSearch>>(
  (ref) => RecentSearchesNotifier(ref.watch(localStoreProvider)),
);

class RecentSearchesNotifier extends StateNotifier<List<RecentSearch>> {
  RecentSearchesNotifier(this._store) : super(const []) {
    _load();
  }

  final LocalStore _store;

  void _load() => state = _store.readRecentSearches();

  Future<void> clear() async {
    await _store.clearRecentSearches();
    state = const [];
  }
}
