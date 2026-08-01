import 'package:dio/dio.dart';

import '../config/api_config.dart';
import 'token_storage.dart';

/// Thrown when a request fails after a refresh attempt - callers should
/// route the user back to the login screen.
class SessionExpiredException implements Exception {}

class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;

  late final Dio dio;
  bool _isRefreshing = false;

  ApiClient._internal() {
    dio = Dio(BaseOptions(
      baseUrl: ApiConfig.baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
      headers: {'Content-Type': 'application/json'},
    ));

    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await TokenStorage.getAccessToken();
        if (token != null && !options.path.contains('/auth/login') && !options.path.contains('/auth/register')) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        if (error.response?.statusCode == 401 && !_isRefreshing) {
          _isRefreshing = true;
          try {
            final refreshed = await _tryRefreshToken();
            _isRefreshing = false;
            if (refreshed) {
              final retryRequest = error.requestOptions;
              final token = await TokenStorage.getAccessToken();
              retryRequest.headers['Authorization'] = 'Bearer $token';
              final response = await dio.fetch(retryRequest);
              return handler.resolve(response);
            }
          } catch (_) {
            _isRefreshing = false;
          }
          await TokenStorage.clear();
          return handler.reject(DioException(
            requestOptions: error.requestOptions,
            error: SessionExpiredException(),
          ));
        }
        handler.next(error);
      },
    ));
  }

  Future<bool> _tryRefreshToken() async {
    final refreshToken = await TokenStorage.getRefreshToken();
    if (refreshToken == null) return false;

    try {
      final response = await Dio(BaseOptions(baseUrl: ApiConfig.baseUrl)).post(
        '/api/auth/refresh',
        data: {'refresh_token': refreshToken},
      );
      await TokenStorage.saveTokens(
        accessToken: response.data['access_token'],
        refreshToken: response.data['refresh_token'],
      );
      return true;
    } catch (_) {
      return false;
    }
  }
}
