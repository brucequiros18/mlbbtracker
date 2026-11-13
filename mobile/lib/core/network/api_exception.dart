import 'package:dio/dio.dart';

/// Stable, user-facing error taxonomy produced by the backend and mapped
/// to friendly copy in the UI.
enum ApiErrorKind {
  network,
  timeout,
  notFound,
  validation,
  unsupported,
  server,
  unknown,
}

class ApiException implements Exception {
  ApiException(this.kind, this.message, {this.statusCode, this.code});

  final ApiErrorKind kind;
  final String message;
  final int? statusCode;
  final String? code;

  factory ApiException.fromDio(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return ApiException(
          ApiErrorKind.timeout,
          'The server took too long to respond. Please try again.',
        );
      case DioExceptionType.connectionError:
        return ApiException(
          ApiErrorKind.network,
          'Cannot reach the server. Check your connection and that the backend is running.',
        );
      case DioExceptionType.badResponse:
        final res = e.response;
        final data = res?.data;
        String? code;
        String message = 'Request failed (${res?.statusCode}).';
        if (data is Map) {
          code = data['code']?.toString();
          message = (data['message'] ?? data['detail'] ?? message).toString();
        }
        final status = res?.statusCode ?? 0;
        final ApiErrorKind kind = switch (status) {
          404 => ApiErrorKind.notFound,
          422 => ApiErrorKind.validation,
          501 => ApiErrorKind.unsupported,
          >= 500 => ApiErrorKind.server,
          _ => ApiErrorKind.unknown,
        };
        return ApiException(kind, message, statusCode: status, code: code);
      case DioExceptionType.cancel:
        return ApiException(ApiErrorKind.unknown, 'Request cancelled.');
      default:
        return ApiException(ApiErrorKind.network, e.message ?? 'Unexpected error.');
    }
  }

  @override
  String toString() => 'ApiException($kind, $message)';
}

/// Maps any error to user-facing copy. Never leaks `toString()` internals to
/// the UI.
String describeError(Object error) {
  if (error is ApiException) {
    return switch (error.kind) {
      ApiErrorKind.network =>
        'Cannot reach the MLBB Tracker server. Check your connection and that the backend is running.',
      ApiErrorKind.timeout => 'The server took too long to respond. Please try again.',
      ApiErrorKind.notFound => "That content isn't available. It may not exist or isn't covered by the data source.",
      ApiErrorKind.validation => 'The request was invalid. Please adjust it and try again.',
      ApiErrorKind.unsupported =>
        "This feature isn't available from public MLBB data sources yet.",
      ApiErrorKind.server => 'The server had a problem. Please try again shortly.',
      ApiErrorKind.unknown => error.message,
    };
  }
  return 'Something went wrong. Please try again.';
}
