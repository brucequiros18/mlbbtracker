import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../features/players/domain/player.dart';

/// Lightweight on-device persistence for recent searches and favourite heroes.
///
/// Only non-sensitive, user-owned preferences are stored here. Tokens would
/// live in secure storage instead.
class LocalStore {
  LocalStore(this._prefs);

  final SharedPreferences _prefs;

  static const _recentKey = 'recent_searches';
  static const _favoritesKey = 'favorite_heroes';
  static const _maxRecent = 10;

  // — Recent searches ————————————————————————————————————————
  List<RecentSearch> readRecentSearches() {
    final raw = _prefs.getString(_recentKey);
    if (raw == null || raw.isEmpty) return const [];
    try {
      final list = jsonDecode(raw) as List;
      return list
          .map((e) => RecentSearch.fromJson(e as Map<String, dynamic>))
          .toList(growable: false);
    } catch (_) {
      return const [];
    }
  }

  Future<void> addRecentSearch(String playerId, String zoneId) async {
    final next = [
      RecentSearch(playerId: playerId, zoneId: zoneId, searchedAt: DateTime.now()),
      ...readRecentSearches()
          .where((r) => !(r.playerId == playerId && r.zoneId == zoneId)),
    ].take(_maxRecent).toList();
    await _prefs.setString(_recentKey, jsonEncode(next.map((e) => e.toJson()).toList()));
  }

  Future<void> clearRecentSearches() => _prefs.remove(_recentKey);

  // — Favourite heroes ———————————————————————————————————————
  Set<int> readFavoriteHeroes() {
    final raw = _prefs.getStringList(_favoritesKey);
    if (raw == null) return <int>{};
    return raw.map(int.tryParse).whereType<int>().toSet();
  }

  Future<void> toggleFavoriteHero(int heroId) async {
    final set = readFavoriteHeroes();
    if (!set.add(heroId)) set.remove(heroId);
    await _prefs.setStringList(_favoritesKey, set.map((e) => e.toString()).toList());
  }

  Future<void> setFavorites(Set<int> ids) async {
    await _prefs.setStringList(_favoritesKey, ids.map((e) => e.toString()).toList());
  }
}

/// Overridden in `main()` once [SharedPreferences] has loaded.
final localStoreProvider = Provider<LocalStore>((ref) {
  throw UnimplementedError('localStoreProvider must be overridden in main()');
});
