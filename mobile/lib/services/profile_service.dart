import 'package:dio/dio.dart';

import '../models/profile.dart';
import '../models/user.dart';
import 'api_client.dart';
import 'auth_service.dart';

class ProfileService {
  final Dio _dio = ApiClient().dio;

  Future<ProfileDetail> getProfile(String userId) async {
    try {
      final response = await _dio.get('/api/profiles/$userId');
      return ProfileDetail.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load profile'));
    }
  }

  Future<ProfileDetail> getProfileByUsername(String username) async {
    try {
      final response = await _dio.get('/api/profiles/username/$username');
      return ProfileDetail.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load profile'));
    }
  }

  Future<User> updateProfile({
    String? firstName,
    String? lastName,
    String? bio,
    String? avatarUrl,
    String? website,
  }) async {
    try {
      final response = await _dio.put('/api/profiles/me', data: {
        if (firstName != null) 'first_name': firstName,
        if (lastName != null) 'last_name': lastName,
        if (bio != null) 'bio': bio,
        if (avatarUrl != null) 'avatar_url': avatarUrl,
        if (website != null) 'website': website,
      });
      return User.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to update profile'));
    }
  }

  /// Toggles follow state - the backend exposes a single endpoint that
  /// follows if not already following, and unfollows otherwise.
  Future<bool> toggleFollow(String userId) async {
    try {
      final response = await _dio.post('/api/profiles/$userId/follow');
      return response.data['is_following'] as bool;
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to update follow status'));
    }
  }

  Future<List<User>> getFollowers(String userId, {int limit = 20, int offset = 0}) async {
    try {
      final response = await _dio.get('/api/profiles/$userId/followers', queryParameters: {
        'limit': limit,
        'offset': offset,
      });
      final items = response.data['users'] as List;
      return items.map((e) => User.fromJson(e as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load followers'));
    }
  }

  Future<List<User>> getFollowing(String userId, {int limit = 20, int offset = 0}) async {
    try {
      final response = await _dio.get('/api/profiles/$userId/following', queryParameters: {
        'limit': limit,
        'offset': offset,
      });
      final items = response.data['users'] as List;
      return items.map((e) => User.fromJson(e as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load following'));
    }
  }

  /// Toggles block state - returns the new is_blocked value.
  Future<bool> toggleBlock(String userId) async {
    try {
      final response = await _dio.post('/api/profiles/$userId/block');
      return response.data['is_blocked'] as bool;
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to update block status'));
    }
  }

  Future<List<User>> getBlockedUsers() async {
    try {
      final response = await _dio.get('/api/profiles/me/blocked');
      final items = response.data['users'] as List;
      return items.map((e) => User.fromJson(e as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load blocked users'));
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
