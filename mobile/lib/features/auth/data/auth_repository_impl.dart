import 'package:dio/dio.dart';

import '../../../core/network/api_exception.dart';
import '../domain/account.dart';
import '../domain/auth_repository.dart';

class AuthRepositoryImpl implements AuthRepository {
  AuthRepositoryImpl(this._dio);

  final Dio _dio;

  Map<String, String> _auth(String token) => {'authorization': 'Bearer $token'};

  @override
  Future<AuthConfig> config() async {
    try {
      final res = await _dio.get<Map<String, dynamic>>('/auth/config');
      final data = res.data?['data'] as Map<String, dynamic>?;
      if (data == null) {
        throw ApiException(ApiErrorKind.server, 'The server returned no sign-in configuration.');
      }
      return AuthConfig.fromJson(data);
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  @override
  Future<AuthSessionResult> signInWithGoogle(String credential) async {
    try {
      final res = await _dio.post<Map<String, dynamic>>(
        '/auth/google',
        data: {'credential': credential},
      );
      final data = res.data?['data'] as Map<String, dynamic>?;
      if (data == null) {
        throw ApiException(ApiErrorKind.server, 'The server returned no session.');
      }
      return AuthSessionResult.fromJson(data);
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  @override
  Future<Account> register({
    required String token,
    required String username,
    required String mlbbId,
    required String password,
  }) async {
    try {
      final res = await _dio.post<Map<String, dynamic>>(
        '/auth/register',
        data: {'username': username, 'mlbbId': mlbbId, 'password': password},
        options: Options(headers: _auth(token)),
      );
      return _account(res);
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  @override
  Future<Account> me(String token) async {
    try {
      final res = await _dio.get<Map<String, dynamic>>(
        '/auth/me',
        options: Options(headers: _auth(token)),
      );
      return _account(res);
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  @override
  Future<Account> updateProfile({
    required String token,
    String? username,
    String? mlbbId,
    required String currentPassword,
    String? newPassword,
  }) async {
    try {
      final res = await _dio.patch<Map<String, dynamic>>(
        '/auth/me',
        data: {
          'username': ?username,
          'mlbbId': ?mlbbId,
          'currentPassword': currentPassword,
          'newPassword': ?newPassword,
        },
        options: Options(headers: _auth(token)),
      );
      return _account(res);
    } on DioException catch (e) {
      throw ApiException.fromDio(e);
    }
  }

  @override
  Future<void> logout(String token) async {
    try {
      await _dio.post<Map<String, dynamic>>(
        '/auth/logout',
        options: Options(headers: _auth(token)),
      );
    } on DioException catch (e) {
      // A missing/expired session is already signed out from the app's view.
      final api = ApiException.fromDio(e);
      if (api.kind != ApiErrorKind.unauthorized) throw api;
    }
  }

  Account _account(Response<Map<String, dynamic>> res) {
    final data = res.data?['data'] as Map<String, dynamic>?;
    if (data == null) {
      throw ApiException(ApiErrorKind.server, 'The server returned no account.');
    }
    return Account.fromJson(data);
  }
}
