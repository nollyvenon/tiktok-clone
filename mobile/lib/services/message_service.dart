import 'package:dio/dio.dart';

import '../models/message.dart';
import 'api_client.dart';
import 'auth_service.dart';

class MessageService {
  final Dio _dio = ApiClient().dio;

  Future<List<Conversation>> getConversations({int limit = 50, int offset = 0}) async {
    try {
      final response = await _dio.get('/api/messages/conversations', queryParameters: {
        'limit': limit,
        'offset': offset,
      });
      return (response.data['conversations'] as List)
          .map((e) => Conversation.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load conversations'));
    }
  }

  Future<Conversation> startConversation(String recipientId) async {
    try {
      final response = await _dio.post('/api/messages/conversations', queryParameters: {
        'recipient_id': recipientId,
      });
      return Conversation.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to start conversation'));
    }
  }

  Future<List<ChatMessage>> getMessages(String conversationId, {int limit = 50, int offset = 0}) async {
    try {
      final response = await _dio.get(
        '/api/messages/conversations/$conversationId/messages',
        queryParameters: {'limit': limit, 'offset': offset},
      );
      return (response.data['messages'] as List)
          .map((e) => ChatMessage.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load messages'));
    }
  }

  Future<ChatMessage> sendMessage(String conversationId, String content) async {
    try {
      final response = await _dio.post(
        '/api/messages/conversations/$conversationId/messages',
        data: {'content': content},
      );
      return ChatMessage.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to send message'));
    }
  }

  Future<void> markRead(String conversationId) async {
    try {
      await _dio.put('/api/messages/conversations/$conversationId/read');
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to mark conversation read'));
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
