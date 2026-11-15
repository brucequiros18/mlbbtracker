import 'package:dio/dio.dart';

import '../../../core/network/api_exception.dart';
import '../domain/player.dart';
import '../domain/player_repository.dart';

class PlayerRepositoryImpl implements PlayerRepository {
  PlayerRepositoryImpl(this._dio);

  final Dio _dio;

  Map<String, String> _auth(String token) => {'authorization': 'Bearer $token'};

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

  @override
  Future<void> connectStart({
    required String playerId,
    required String zoneId,
  }) async {
    try {
      await _dio.post<Map<String, dynamic>>(
        '/players/connect/start',
        data: {'playerId': playerId, 'zoneId': zoneId},
      );
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  @override
  Future<ConnectResult> connectVerify({
    required String playerId,
    required String zoneId,
    required String code,
  }) async {
    try {
      final res = await _dio.post<Map<String, dynamic>>(
        '/players/connect/verify',
        data: {'playerId': playerId, 'zoneId': zoneId, 'code': code},
      );
      final data = res.data?['data'] as Map<String, dynamic>?;
      if (data == null) {
        throw ApiException(ApiErrorKind.server, 'The server returned no session.');
      }
      return ConnectResult(
        sessionToken: data['sessionToken'] as String,
        player: PlayerProfile.fromJson(data['player'] as Map<String, dynamic>),
      );
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  @override
  Future<void> disconnect(String sessionToken) async {
    try {
      await _dio.post<Map<String, dynamic>>(
        '/players/disconnect',
        options: Options(headers: _auth(sessionToken)),
      );
    } on DioException catch (e) {
      // A missing/expired session is already "disconnected" from the app's
      // perspective; only surface real transport/server failures.
      final api = ApiException.fromDio(e);
      if (api.kind != ApiErrorKind.unauthorized) throw api;
    }
  }

  @override
  Future<PlayerProfile> profile(String sessionToken) async {
    final data = await _getData('/players/me/profile', sessionToken);
    return PlayerProfile.fromJson(data);
  }

  @override
  Future<PlayerStats> stats(String sessionToken) async {
    final data = await _getData('/players/me/stats', sessionToken);
    return PlayerStats.fromJson(data);
  }

  @override
  Future<PlayerMatchesPage> matches(
    String sessionToken, {
    int limit = 20,
    String? cursor,
  }) async {
    try {
      final res = await _dio.get<Map<String, dynamic>>(
        '/players/me/matches',
        queryParameters: {'limit': limit, 'cursor': ?cursor},
        options: Options(headers: _auth(sessionToken)),
      );
      final data = res.data?['data'] as Map<String, dynamic>?;
      if (data == null) {
        throw ApiException(ApiErrorKind.server, 'The server returned no matches.');
      }
      return PlayerMatchesPage.fromJson(data);
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  @override
  Future<List<FrequentHero>> frequentHeroes(String sessionToken, {int limit = 10}) async {
    try {
      final res = await _dio.get<Map<String, dynamic>>(
        '/players/me/heroes',
        queryParameters: {'limit': limit},
        options: Options(headers: _auth(sessionToken)),
      );
      final list = (res.data?['data'] as List?) ?? const [];
      return list
          .map((e) => FrequentHero.fromJson(e as Map<String, dynamic>))
          .toList(growable: false);
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  Future<Map<String, dynamic>> _getData(String path, String token) async {
    try {
      final res = await _dio.get<Map<String, dynamic>>(
        path,
        options: Options(headers: _auth(token)),
      );
      final data = res.data?['data'] as Map<String, dynamic>?;
      if (data == null) {
        throw ApiException(ApiErrorKind.server, 'The server returned an empty response.');
      }
      return data;
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }
}
