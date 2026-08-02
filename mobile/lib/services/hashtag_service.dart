import 'package:dio/dio.dart';

import '../models/hashtag_trend.dart';
import '../models/video.dart';
import 'api_client.dart';
import 'auth_service.dart';

class HashtagAnalyticsPoint {
  final String date;
  final int usageCount;

  HashtagAnalyticsPoint({required this.date, required this.usageCount});

  factory HashtagAnalyticsPoint.fromJson(Map<String, dynamic> json) {
    return HashtagAnalyticsPoint(
      date: json['date'] as String,
      usageCount: json['usage_count'] as int,
    );
  }
}

class HashtagService {
  final Dio _dio = ApiClient().dio;

  Future<List<HashtagTrend>> getTrending({String region = 'US', int limit = 20}) async {
    try {
      final response = await _dio.get('/api/hashtags/trending', queryParameters: {
        'region': region,
        'limit': limit,
      });
      return (response.data as List)
          .map((e) => HashtagTrend.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load trending hashtags'));
    }
  }

  Future<List<Challenge>> getActiveChallenges({String region = 'US', int limit = 10}) async {
    try {
      final response = await _dio.get('/api/hashtags/challenges/active', queryParameters: {
        'region': region,
        'limit': limit,
      });
      return (response.data as List)
          .map((e) => Challenge.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load challenges'));
    }
  }

  Future<Challenge> getChallengeDetails(String challengeId) async {
    try {
      final response = await _dio.get('/api/hashtags/challenges/$challengeId');
      return Challenge.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load challenge'));
    }
  }

  Future<(List<Video>, int)> getChallengeVideos(String challengeId, {int limit = 30, int offset = 0}) async {
    try {
      final response = await _dio.get('/api/hashtags/challenges/$challengeId/videos', queryParameters: {
        'limit': limit,
        'offset': offset,
      });
      final videos = (response.data['videos'] as List)
          .map((e) => Video.fromJson(e as Map<String, dynamic>))
          .toList();
      return (videos, response.data['total'] as int);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load challenge videos'));
    }
  }

  Future<Map<String, dynamic>> getStats(String hashtag, {String region = 'US'}) async {
    try {
      final response = await _dio.get(
        '/api/hashtags/${Uri.encodeComponent(hashtag)}/stats',
        queryParameters: {'region': region},
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load hashtag stats'));
    }
  }

  Future<List<HashtagAnalyticsPoint>> getAnalytics(String hashtag, {int days = 30}) async {
    try {
      final response = await _dio.get(
        '/api/hashtags/${Uri.encodeComponent(hashtag)}/analytics',
        queryParameters: {'days': days},
      );
      return (response.data as List)
          .map((e) => HashtagAnalyticsPoint.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load hashtag analytics'));
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
