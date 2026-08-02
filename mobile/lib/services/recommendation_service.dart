import 'package:dio/dio.dart';

import '../models/video.dart';
import 'api_client.dart';
import 'auth_service.dart';

class Recommendation {
  final String id;
  final double score;
  final String algorithm;
  final String? reason;
  final Video video;

  Recommendation({
    required this.id,
    required this.score,
    required this.algorithm,
    this.reason,
    required this.video,
  });

  factory Recommendation.fromJson(Map<String, dynamic> json) {
    return Recommendation(
      id: json['id'] as String,
      score: (json['score'] as num).toDouble(),
      algorithm: json['algorithm'] as String,
      reason: json['reason'] as String?,
      video: Video.fromJson(json['video'] as Map<String, dynamic>),
    );
  }
}

class RecommendationsPage {
  final List<Recommendation> recommendations;
  final String? cursor;

  RecommendationsPage({required this.recommendations, this.cursor});
}

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

  Future<RecommendationsPage> getForYouFeed({int limit = 30, String? cursor}) async {
    try {
      final response = await _dio.get('/api/recommendations/for-you', queryParameters: {
        'limit': limit,
        if (cursor != null) 'cursor': cursor,
      });
      final recommendations = (response.data['recommendations'] as List)
          .map((e) => Recommendation.fromJson(e as Map<String, dynamic>))
          .toList();
      return RecommendationsPage(
        recommendations: recommendations,
        cursor: response.data['cursor'] as String?,
      );
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load For You feed'));
    }
  }

  Future<void> recordFeedback(String recommendationId, String feedbackType) async {
    try {
      await _dio.post('/api/recommendations/$recommendationId/feedback', data: {
        'feedback_type': feedbackType,
      });
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to record feedback'));
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
