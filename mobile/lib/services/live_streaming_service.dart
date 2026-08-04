import 'package:dio/dio.dart';

import '../models/live_stream.dart';
import 'api_client.dart';
import 'auth_service.dart';

class LiveStreamingService {
  final Dio _dio = ApiClient().dio;

  Future<LiveStream> startStream(String title) async {
    try {
      final response = await _dio.post('/api/live/start', data: {'title': title});
      return LiveStream.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to start stream'));
    }
  }

  Future<List<LiveStream>> listLiveStreams() async {
    try {
      final response = await _dio.get('/api/live');
      return (response.data['streams'] as List)
          .map((e) => LiveStream.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load live streams'));
    }
  }

  Future<LiveStream> getStream(String streamId) async {
    try {
      final response = await _dio.get('/api/live/$streamId');
      return LiveStream.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Stream not found'));
    }
  }

  Future<LiveStream> endStream(String streamId) async {
    try {
      final response = await _dio.post('/api/live/$streamId/end');
      return LiveStream.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to end stream'));
    }
  }

  Future<LiveStream> joinStream(String streamId) async {
    try {
      final response = await _dio.post('/api/live/$streamId/join');
      return LiveStream.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to join stream'));
    }
  }

  Future<void> leaveStream(String streamId) async {
    try {
      await _dio.post('/api/live/$streamId/leave');
    } catch (_) {
      // Best-effort: leaving on screen dispose shouldn't surface an error
    }
  }

  Future<LiveChatMessage> postChatMessage(String streamId, String content) async {
    try {
      final response = await _dio.post('/api/live/$streamId/chat', data: {'content': content});
      return LiveChatMessage.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to send message'));
    }
  }

  Future<List<LiveChatMessage>> getChatMessages(String streamId) async {
    try {
      final response = await _dio.get('/api/live/$streamId/chat');
      return (response.data['messages'] as List)
          .map((e) => LiveChatMessage.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load chat'));
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
