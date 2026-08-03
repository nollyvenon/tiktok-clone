import 'package:dio/dio.dart';

import '../models/auth_response.dart';
import '../models/user.dart';
import 'api_client.dart';
import 'token_storage.dart';

class ApiException implements Exception {
  final String message;
  ApiException(this.message);
  @override
  String toString() => message;
}

class TwoFactorRequiredException implements Exception {
  final String pendingToken;
  TwoFactorRequiredException(this.pendingToken);
}

class AuthService {
  final Dio _dio = ApiClient().dio;

  Future<AuthResponse> login(String email, String password) async {
    try {
      final response = await _dio.post('/api/auth/login', data: {
        'email': email,
        'password': password,
      });
      final auth = AuthResponse.fromJson(response.data);
      await TokenStorage.saveTokens(
        accessToken: auth.accessToken,
        refreshToken: auth.refreshToken,
      );
      return auth;
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Login failed'));
    }
  }

  Future<AuthResponse> register({
    required String email,
    required String username,
    required String password,
    String? firstName,
    String? lastName,
  }) async {
    try {
      final response = await _dio.post('/api/auth/register', data: {
        'email': email,
        'username': username,
        'password': password,
        if (firstName != null) 'first_name': firstName,
        if (lastName != null) 'last_name': lastName,
      });
      final auth = AuthResponse.fromJson(response.data);
      await TokenStorage.saveTokens(
        accessToken: auth.accessToken,
        refreshToken: auth.refreshToken,
      );
      return auth;
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Registration failed'));
    }
  }

  Future<void> logout() async {
    try {
      await _dio.post('/api/auth/logout');
    } catch (_) {
      // Best-effort: clear local tokens even if the server call fails
    } finally {
      await TokenStorage.clear();
    }
  }

  Future<User?> getCurrentUser() async {
    final token = await TokenStorage.getAccessToken();
    if (token == null) return null;
    try {
      final response = await _dio.get('/api/auth/me');
      return User.fromJson(response.data);
    } on DioException {
      return null;
    }
  }

  Future<Map<String, dynamic>> setup2FA() async {
    try {
      final response = await _dio.post('/api/auth/2fa/setup');
      return response.data;
    } on DioException catch (e) {
      throw ApiException(_extractError(e, '2FA setup failed'));
    }
  }

  Future<void> verify2FA(String code) async {
    try {
      await _dio.post('/api/auth/2fa/verify', data: {'code': code});
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Invalid 2FA code'));
    }
  }

  Future<void> disable2FA() async {
    try {
      await _dio.post('/api/auth/2fa/disable');
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to disable 2FA'));
    }
  }

  Future<void> requestPasswordReset(String email) async {
    try {
      await _dio.post('/api/auth/password-reset', data: {'email': email});
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to request password reset'));
    }
  }

  Future<void> changePassword(String currentPassword, String newPassword, String confirmPassword) async {
    try {
      await _dio.post('/api/auth/change-password', data: {
        'current_password': currentPassword,
        'new_password': newPassword,
        'confirm_password': confirmPassword,
      });
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to change password'));
    }
  }

  Future<Map<String, dynamic>> exportMyData() async {
    try {
      final response = await _dio.get('/api/auth/me/export');
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to export data'));
    }
  }

  Future<void> deleteAccount(String password) async {
    try {
      await _dio.delete('/api/auth/me', data: {'password': password});
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to delete account'));
    }
  }

  String _extractError(DioException e, String fallback) {
    final data = e.response?.data;
    if (data is Map && data['detail'] != null) {
      return data['detail'].toString();
    }
    return fallback;
  }
}
