import 'package:dio/dio.dart';

import '../../../core/network/api_exception.dart';
import '../domain/player.dart';
import '../domain/player_repository.dart';

class PlayerRepositoryImpl implements PlayerRepository {
  PlayerRepositoryImpl(this._dio);

  final Dio _dio;

  @override
  Future<PlayerProfile> lookup({
    required String playerId,
    required String zoneId,
  }) async {
    try {
      final res = await _dio.get<Map<String, dynamic>>('/players/$playerId/$zoneId');
      final data = res.data?['data'] as Map<String, dynamic>?;
      if (data == null) {
        throw ApiException(ApiErrorKind.notFound, 'Player not found.');
      }
      return PlayerProfile.fromJson(data);
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }
}
