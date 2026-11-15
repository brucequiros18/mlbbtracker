import 'package:flutter/foundation.dart';

/// Runtime configuration for the backend API.
///
/// The Flutter app never talks to a third-party MLBB provider directly and
/// never holds provider credentials — every request goes through the MLBB
/// Tracker FastAPI backend, which owns the provider adapters.
///
/// Override the base URL at build time with:
///   flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000
abstract final class ApiConfig {
  /// Resolved per target:
  ///  * Web              → the origin the app is served from (same origin as
  ///                       the API, so no CORS configuration is needed)
  ///  * Android emulator → 10.0.2.2 (the host loopback alias)
  ///  * Desktop          → localhost
  ///
  /// A `--dart-define=API_BASE_URL=…` always wins, which is how you point the
  /// app at a separate API host (or a physical device at a machine on your LAN).
  static final String baseUrl = _resolve();

  static String _resolve() {
    const override = String.fromEnvironment('API_BASE_URL');
    if (override.isNotEmpty) return override;
    if (kIsWeb) {
      // Same-origin by default: the backend serves the web build, so requests
      // to /api/v1 work on whatever host the app is deployed to.
      try {
        return Uri.base.origin;
      } catch (_) {
        return 'http://localhost:8000';
      }
    }
    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000';
    }
    return 'http://localhost:8000';
  }

  static const String apiPrefix = '/api/v1';

  static const Duration connectTimeout = Duration(seconds: 12);
  static const Duration receiveTimeout = Duration(seconds: 20);

  /// When true the app shows a banner reminding testers that player
  /// statistics are unavailable from public sources. Development only.
  static const bool isDev = bool.fromEnvironment('dart.vm.product') == false;
}
