import 'package:dio/dio.dart';

import 'api_client.dart';
import 'auth_service.dart';

class UserPreferences {
  final String id;
  final List<String> preferredHashtags;
  final double contentDiversityScore;
  final double recencyPreference;
  final int? avgWatchTime;

  UserPreferences({
    required this.id,
    required this.preferredHashtags,
    required this.contentDiversityScore,
    required this.recencyPreference,
    this.avgWatchTime,
  });

  factory UserPreferences.fromJson(Map<String, dynamic> json) {
    return UserPreferences(
      id: json['id'] as String,
      preferredHashtags: (json['preferred_hashtags'] as List?)?.map((e) => e as String).toList() ?? [],
      contentDiversityScore: (json['content_diversity_score'] as num).toDouble(),
      recencyPreference: (json['recency_preference'] as num).toDouble(),
      avgWatchTime: json['avg_watch_time'] as int?,
    );
  }
}

class RecommendationService {
  final Dio _dio = ApiClient().dio;

  Future<UserPreferences> getPreferences() async {
    try {
      final response = await _dio.get('/api/recommendations/preferences');
      return UserPreferences.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load preferences'));
    }
  }

  Future<UserPreferences> updatePreferences({
    double? contentDiversityScore,
    double? recencyPreference,
    List<String>? preferredHashtags,
  }) async {
    try {
      final response = await _dio.put('/api/recommendations/preferences', data: {
        if (contentDiversityScore != null) 'content_diversity_score': contentDiversityScore,
        if (recencyPreference != null) 'recency_preference': recencyPreference,
        if (preferredHashtags != null) 'preferred_hashtags': preferredHashtags,
      });
      return UserPreferences.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to save preferences'));
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
