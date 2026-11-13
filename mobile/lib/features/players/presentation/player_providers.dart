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

sealed class PlayerSearchState {
  const PlayerSearchState();
}

class PlayerSearchIdle extends PlayerSearchState {
  const PlayerSearchIdle();
}

class PlayerSearchLoading extends PlayerSearchState {
  const PlayerSearchLoading();
}

class PlayerSearchSuccess extends PlayerSearchState {
  const PlayerSearchSuccess(this.profile);
  final PlayerProfile profile;
}

/// No permitted data source can serve this player. Carries an explanation.
class PlayerSearchUnavailable extends PlayerSearchState {
  const PlayerSearchUnavailable(this.message);
  final String message;
}

class PlayerSearchFailure extends PlayerSearchState {
  const PlayerSearchFailure(this.message);
  final String message;
}

class PlayerSearchController extends StateNotifier<PlayerSearchState> {
  PlayerSearchController(this._repo, this._store)
      : super(const PlayerSearchIdle());

  final PlayerRepository _repo;
  final LocalStore _store;

  Future<void> search(String playerId, String zoneId) async {
    state = const PlayerSearchLoading();
    try {
      final profile = await _repo.lookup(playerId: playerId, zoneId: zoneId);
      await _store.addRecentSearch(playerId, zoneId);
      state = PlayerSearchSuccess(profile);
    } on ApiException catch (e) {
      if (e.kind == ApiErrorKind.unsupported) {
        state = PlayerSearchUnavailable(e.message);
      } else {
        state = PlayerSearchFailure(e.message);
      }
    } catch (e) {
      state = PlayerSearchFailure('Unexpected error: $e');
    }
  }

  void reset() => state = const PlayerSearchIdle();
}

final playerSearchControllerProvider =
    StateNotifierProvider.autoDispose<PlayerSearchController, PlayerSearchState>(
  (ref) => PlayerSearchController(
    ref.watch(playerRepositoryProvider),
    ref.watch(localStoreProvider),
  ),
);

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
