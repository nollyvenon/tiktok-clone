/// API configuration for the backend base URL.
///
/// Android emulators reach the host machine's localhost via 10.0.2.2, not
/// 127.0.0.1 - use --dart-define=API_BASE_URL=... to override per platform.
class ApiConfig {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );
}
