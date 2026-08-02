import 'package:dio/dio.dart';

import 'api_client.dart';
import 'auth_service.dart';

class ModerationService {
  final Dio _dio = ApiClient().dio;

  Future<void> createReport({
    required String contentType,
    required String contentId,
    required String reason,
    String? description,
  }) async {
    try {
      await _dio.post('/api/moderation/reports', data: {
        'content_type': contentType,
        'content_id': contentId,
        'reason': reason,
        if (description != null && description.isNotEmpty) 'description': description,
      });
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to submit report'));
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
