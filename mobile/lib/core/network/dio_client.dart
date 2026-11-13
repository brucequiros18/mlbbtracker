import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/api_config.dart';

/// A configured [Dio] instance shared by every repository.
///
/// Adds the API prefix, JSON headers, sane timeouts, and normalises transport
/// errors into a single, typed failure surface.
Dio buildDio({String? baseUrl}) {
  final dio = Dio(
    BaseOptions(
      baseUrl: '${baseUrl ?? ApiConfig.baseUrl}${ApiConfig.apiPrefix}',
      connectTimeout: ApiConfig.connectTimeout,
      receiveTimeout: ApiConfig.receiveTimeout,
      headers: const {'accept': 'application/json'},
      responseType: ResponseType.json,
    ),
  );
  return dio;
}

/// Exposes the shared Dio client. Overridden in tests with a mock adapter.
final dioProvider = Provider<Dio>((ref) => buildDio());
