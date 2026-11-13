import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../shared/local/local_store.dart';

/// Set of favourite hero ids, persisted on-device.
final favoriteHeroesProvider =
    StateNotifierProvider<FavoriteHeroesNotifier, Set<int>>(
  (ref) => FavoriteHeroesNotifier(ref.watch(localStoreProvider)),
);

class FavoriteHeroesNotifier extends StateNotifier<Set<int>> {
  FavoriteHeroesNotifier(this._store) : super(_store.readFavoriteHeroes());

  final LocalStore _store;

  Future<void> toggle(int heroId) async {
    await _store.toggleFavoriteHero(heroId);
    state = _store.readFavoriteHeroes();
  }

  bool isFavorite(int heroId) => state.contains(heroId);
}
