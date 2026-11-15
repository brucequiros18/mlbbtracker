import 'player.dart';

abstract interface class PlayerRepository {
  /// Anonymous lookup by Player ID + Zone ID.
  ///
  /// Throws an `ApiException` of kind `unsupported` — no permitted source
  /// serves another player's stats without consent.
  Future<PlayerProfile> lookup({required String playerId, required String zoneId});

  // — Consented connect flow —————————————————————————————————
  /// Step 1: ask the provider to send a one-time code to the in-game mailbox.
  Future<void> connectStart({required String playerId, required String zoneId});

  /// Step 2: exchange the code for an opaque backend session token.
  Future<ConnectResult> connectVerify({
    required String playerId,
    required String zoneId,
    required String code,
  });

  Future<void> disconnect(String sessionToken);

  Future<PlayerProfile> profile(String sessionToken);

  Future<PlayerStats> stats(String sessionToken);

  Future<PlayerMatchesPage> matches(
    String sessionToken, {
    int limit = 20,
    String? cursor,
  });

  Future<List<FrequentHero>> frequentHeroes(String sessionToken, {int limit = 10});
}
