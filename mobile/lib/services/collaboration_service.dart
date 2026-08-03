import 'package:dio/dio.dart';

import '../models/collaboration.dart';
import 'api_client.dart';
import 'auth_service.dart';

class CollaborationService {
  final Dio _dio = ApiClient().dio;

  Future<Collaboration> create({
    required String videoId,
    String? title,
    required List<Map<String, dynamic>> collaborators,
  }) async {
    try {
      final response = await _dio.post('/api/collaborations', data: {
        'video_id': videoId,
        if (title != null && title.isNotEmpty) 'title': title,
        'collaborators': collaborators,
      });
      return Collaboration.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to create collaboration'));
    }
  }

  Future<List<Collaboration>> listMine() async {
    try {
      final response = await _dio.get('/api/collaborations/me');
      return (response.data as List)
          .map((e) => Collaboration.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load your collaborations'));
    }
  }

  Future<Collaboration> respond(String collaborationId, bool accept) async {
    try {
      final response = await _dio.post(
        '/api/collaborations/$collaborationId/respond',
        data: {'accept': accept},
      );
      return Collaboration.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to respond'));
    }
  }

  Future<Collaboration> cancel(String collaborationId) async {
    try {
      final response = await _dio.post('/api/collaborations/$collaborationId/cancel');
      return Collaboration.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to cancel'));
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
