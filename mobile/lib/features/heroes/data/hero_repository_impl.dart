import 'package:dio/dio.dart';

import '../../../core/network/api_exception.dart';
import '../domain/hero.dart';
import '../domain/hero_repository.dart';

/// Dio-backed [HeroRepository] that talks to the MLBB Tracker backend.
class HeroRepositoryImpl implements HeroRepository {
  HeroRepositoryImpl(this._dio);

  final Dio _dio;

  @override
  Future<List<HeroSummary>> listHeroes({String? role, String? lane}) async {
    try {
      final res = await _dio.get<Map<String, dynamic>>(
        '/heroes',
        queryParameters: {
          if (role != null && role != 'All') 'role': role,
          if (lane != null && lane != 'All') 'lane': lane,
        },
      );
      final data = (res.data?['data'] as List?) ?? const [];
      return data
          .map((e) => HeroSummary.fromJson(e as Map<String, dynamic>))
          .toList(growable: false);
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  @override
  Future<HeroDetail> getHero(String identifier) async {
    try {
      final res = await _dio.get<Map<String, dynamic>>('/heroes/$identifier');
      final data = res.data?['data'] as Map<String, dynamic>?;
      if (data == null) {
        throw ApiException(ApiErrorKind.notFound, 'Hero not found.');
      }
      return HeroDetail.fromJson(data);
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  @override
  Future<List<HeroRankStat>> heroRankings({
    int days = 7,
    String rank = 'all',
    String sortField = 'win_rate',
  }) async {
    try {
      final res = await _dio.get<Map<String, dynamic>>(
        '/heroes/rankings',
        queryParameters: {'days': days, 'rank': rank, 'sort': sortField},
      );
      final data = (res.data?['data'] as List?) ?? const [];
      return data
          .map((e) => HeroRankStat.fromJson(e as Map<String, dynamic>))
          .toList(growable: false);
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }
}
