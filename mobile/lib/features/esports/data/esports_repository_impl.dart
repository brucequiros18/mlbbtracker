import 'package:dio/dio.dart';

import '../../../core/network/api_exception.dart';
import '../domain/standing.dart';
import '../domain/esports_repository.dart';

class EsportsRepositoryImpl implements EsportsRepository {
  EsportsRepositoryImpl(this._dio);

  final Dio _dio;

  @override
  Future<List<EsportsStanding>> standings(String league) async {
    try {
      final res = await _dio.get<Map<String, dynamic>>(
        '/esports/$league/standings',
      );
      final data = (res.data?['data'] as List?) ?? const [];
      return data
          .map((e) => EsportsStanding.fromJson(e as Map<String, dynamic>))
          .toList(growable: false);
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }
}
