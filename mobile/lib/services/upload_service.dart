import 'dart:io';

import 'package:dio/dio.dart';

import '../models/draft.dart';
import 'api_client.dart';
import 'auth_service.dart';

class UploadService {
  final Dio _dio = ApiClient().dio;

  Future<Map<String, dynamic>> getPresignedUrl(String filename, int fileSize, String mimeType) async {
    try {
      final response = await _dio.post('/api/uploads/presigned-url', data: {
        'filename': filename,
        'file_size': fileSize,
        'mime_type': mimeType,
      });
      return response.data;
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to prepare upload'));
    }
  }

  /// Uploads the raw file bytes directly to the presigned URL, reporting
  /// progress via [onProgress] (0.0-1.0).
  Future<void> uploadFile(String presignedUrl, File file, String mimeType, {
    void Function(double progress)? onProgress,
  }) async {
    try {
      await Dio().put(
        presignedUrl,
        data: file.openRead(),
        options: Options(
          headers: {
            'Content-Type': mimeType,
            Headers.contentLengthHeader: await file.length(),
          },
        ),
        onSendProgress: (sent, total) {
          if (total > 0) onProgress?.call(sent / total);
        },
      );
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Upload failed'));
    }
  }

  Future<void> completeUpload(
    String uploadId,
    String processedVideoUrl,
    String thumbnailUrl,
    int duration,
  ) async {
    try {
      await _dio.post(
        '/api/uploads/$uploadId/complete',
        queryParameters: {
          'processed_video_url': processedVideoUrl,
          'thumbnail_url': thumbnailUrl,
          'duration': duration,
        },
      );
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to finalize upload'));
    }
  }

  Future<Draft> createDraft({
    required String uploadId,
    String? title,
    String? description,
    bool isPublic = true,
    String? originalVideoId,
    String? remixType,
  }) async {
    try {
      final response = await _dio.post(
        '/api/uploads/drafts',
        data: {
          if (title != null) 'title': title,
          if (description != null) 'description': description,
          'is_public': isPublic,
          if (originalVideoId != null) 'original_video_id': originalVideoId,
          if (remixType != null) 'remix_type': remixType,
        },
        queryParameters: {'upload_id': uploadId},
      );
      return Draft.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to create draft'));
    }
  }

  Future<List<Draft>> getUserDrafts({int limit = 20, int offset = 0}) async {
    try {
      final response = await _dio.get('/api/uploads/drafts', queryParameters: {
        'limit': limit,
        'offset': offset,
      });
      final items = response.data['drafts'] as List;
      return items.map((e) => Draft.fromJson(e as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load drafts'));
    }
  }

  Future<void> publishDraft(String draftId) async {
    try {
      await _dio.post('/api/uploads/drafts/$draftId/publish');
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to publish draft'));
    }
  }

  Future<void> scheduleDraft(String draftId, DateTime publishAt) async {
    try {
      await _dio.post(
        '/api/uploads/drafts/$draftId/schedule',
        queryParameters: {'publish_at': publishAt.toIso8601String()},
      );
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to schedule draft'));
    }
  }

  Future<void> deleteDraft(String draftId) async {
    try {
      await _dio.delete('/api/uploads/drafts/$draftId');
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to delete draft'));
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
