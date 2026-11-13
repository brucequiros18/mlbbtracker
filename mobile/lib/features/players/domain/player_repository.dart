import 'player.dart';

abstract interface class PlayerRepository {
  /// Looks up a player by Player ID + Zone ID.
  ///
  /// Throws an `ApiException` of kind `unsupported` when no permitted source
  /// can serve the data.
  Future<PlayerProfile> lookup({required String playerId, required String zoneId});
}
