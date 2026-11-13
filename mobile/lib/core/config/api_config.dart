/// Runtime configuration for the backend API.
///
/// The Flutter app never talks to a third-party MLBB provider directly and
/// never holds provider credentials — every request goes through the MLBB
/// Tracker FastAPI backend, which owns the provider adapters.
///
/// Override the base URL at build time with:
///   flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000
abstract final class ApiConfig {
  /// Android emulators reach the host machine through 10.0.2.2.
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  static const String apiPrefix = '/api/v1';

  static const Duration connectTimeout = Duration(seconds: 12);
  static const Duration receiveTimeout = Duration(seconds: 20);

  /// When true the app shows a banner reminding testers that player
  /// statistics are unavailable from public sources. Development only.
  static const bool isDev = bool.fromEnvironment('dart.vm.product') == false;
}
