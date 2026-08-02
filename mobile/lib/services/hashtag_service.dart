import 'package:dio/dio.dart';

import '../models/hashtag_trend.dart';
import 'api_client.dart';
import 'auth_service.dart';

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

  String _extractError(DioException e, String fallback) {
    final data = e.response?.data;
    if (data is Map && data['detail'] != null) {
      return data['detail'].toString();
    }
    return fallback;
  }
}
