import 'package:dio/dio.dart';

import '../models/editor_state.dart';
import 'api_client.dart';
import 'auth_service.dart';

class EditorService {
  final Dio _dio = ApiClient().dio;

  Future<EditorStateData> getEditorState(String draftId) async {
    try {
      final response = await _dio.get('/api/editor/drafts/$draftId/state');
      return EditorStateData.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load editor state'));
    }
  }

  Future<EditorSegment> applyEffect(String segmentId, String effectName) async {
    try {
      final response = await _dio.post('/api/editor/segments/$segmentId/effects/$effectName');
      return EditorSegment.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to apply effect'));
    }
  }

  Future<EditorSegment> adjustSpeed(String segmentId, double speed) async {
    try {
      final response = await _dio.post(
        '/api/editor/segments/$segmentId/speed',
        queryParameters: {'speed': speed},
      );
      return EditorSegment.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to adjust speed'));
    }
  }

  Future<EditorSegment> adjustVolume(String segmentId, int volume) async {
    try {
      final response = await _dio.post(
        '/api/editor/segments/$segmentId/volume',
        queryParameters: {'volume': volume},
      );
      return EditorSegment.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to adjust volume'));
    }
  }

  Future<EditorSegment> muteSegment(String segmentId, bool muted) async {
    try {
      final response = await _dio.post(
        '/api/editor/segments/$segmentId/mute',
        queryParameters: {'muted': muted},
      );
      return EditorSegment.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to mute segment'));
    }
  }

  Future<void> deleteSegment(String segmentId) async {
    try {
      await _dio.delete('/api/editor/segments/$segmentId');
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to delete segment'));
    }
  }

  Future<void> addTextOverlay(String segmentId, String text) async {
    try {
      await _dio.post('/api/editor/segments/$segmentId/overlays', data: {
        'text': text,
        'x': 50,
        'y': 50,
        'width': 200,
        'height': 60,
      });
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to add text overlay'));
    }
  }

  Future<Map<String, dynamic>> exportVideo(String draftId, {String quality = '1080p', String format = 'mp4'}) async {
    try {
      final response = await _dio.post(
        '/api/editor/drafts/$draftId/export',
        queryParameters: {'quality': quality, 'format': format},
      );
      return response.data;
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to export video'));
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
