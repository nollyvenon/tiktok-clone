import 'package:flutter/foundation.dart';

import '../models/user.dart';
import '../services/auth_service.dart';
import '../services/token_storage.dart';

enum AuthStatus { unknown, authenticated, unauthenticated }

class AuthProvider extends ChangeNotifier {
  final AuthService _authService = AuthService();

  AuthStatus status = AuthStatus.unknown;
  User? user;
  String? error;
  bool isLoading = false;

  Future<void> bootstrap() async {
    final token = await TokenStorage.getAccessToken();
    if (token == null) {
      status = AuthStatus.unauthenticated;
      notifyListeners();
      return;
    }

    final fetchedUser = await _authService.getCurrentUser();
    if (fetchedUser != null) {
      user = fetchedUser;
      status = AuthStatus.authenticated;
    } else {
      status = AuthStatus.unauthenticated;
    }
    notifyListeners();
  }

  Future<bool> login(String email, String password) async {
    isLoading = true;
    error = null;
    notifyListeners();

    try {
      final auth = await _authService.login(email, password);
      user = auth.user;
      status = AuthStatus.authenticated;
      return true;
    } catch (e) {
      error = e.toString();
      return false;
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> register({
    required String email,
    required String username,
    required String password,
    String? firstName,
    String? lastName,
  }) async {
    isLoading = true;
    error = null;
    notifyListeners();

    try {
      final auth = await _authService.register(
        email: email,
        username: username,
        password: password,
        firstName: firstName,
        lastName: lastName,
      );
      user = auth.user;
      status = AuthStatus.authenticated;
      return true;
    } catch (e) {
      error = e.toString();
      return false;
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await _authService.logout();
    user = null;
    status = AuthStatus.unauthenticated;
    notifyListeners();
  }

  void clearError() {
    error = null;
    notifyListeners();
  }
}
