import 'package:dio/dio.dart';

import '../models/comment.dart';
import 'api_client.dart';
import 'auth_service.dart';

class CommentService {
  final Dio _dio = ApiClient().dio;

  Future<CommentPage> getComments(String videoId, {int limit = 20, int offset = 0}) async {
    try {
      final response = await _dio.get('/api/videos/$videoId/comments', queryParameters: {
        'limit': limit,
        'offset': offset,
      });
      return CommentPage.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load comments'));
    }
  }

  Future<CommentPage> getReplies(String commentId, {int limit = 20, int offset = 0}) async {
    try {
      final response = await _dio.get('/api/comments/$commentId/replies', queryParameters: {
        'limit': limit,
        'offset': offset,
      });
      return CommentPage.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load replies'));
    }
  }

  Future<Comment> createComment(String videoId, String content, {String? parentCommentId}) async {
    try {
      final response = await _dio.post('/api/videos/$videoId/comments', data: {
        'content': content,
        if (parentCommentId != null) 'parent_comment_id': parentCommentId,
      });
      return Comment.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to post comment'));
    }
  }

  Future<Comment> updateComment(String commentId, String content) async {
    try {
      final response = await _dio.put('/api/comments/$commentId', data: {'content': content});
      return Comment.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to edit comment'));
    }
  }

  Future<void> deleteComment(String commentId) async {
    try {
      await _dio.delete('/api/comments/$commentId');
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to delete comment'));
    }
  }

  Future<Map<String, dynamic>> toggleLike(String commentId) async {
    try {
      final response = await _dio.post('/api/comments/$commentId/like');
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to like comment'));
    }
  }

  Future<Comment> togglePin(String commentId) async {
    try {
      final response = await _dio.post('/api/comments/$commentId/pin');
      return Comment.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to pin comment'));
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
