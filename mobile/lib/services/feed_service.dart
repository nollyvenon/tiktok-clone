import 'package:dio/dio.dart';

import '../models/video.dart';
import '../models/dashboard.dart';
import 'api_client.dart';
import 'auth_service.dart';

class FeedPage {
  final List<Video> videos;
  final int? total;

  FeedPage({required this.videos, this.total});
}

class FeedService {
  final Dio _dio = ApiClient().dio;

  /// The backend paginates the feed by offset (its `cursor` response field
  /// is not yet implemented server-side and is always null).
  Future<FeedPage> getFeed({String feedType = 'for_you', int limit = 10, int offset = 0}) async {
    try {
      final response = await _dio.get('/api/videos/feed', queryParameters: {
        'feed_type': feedType,
        'limit': limit,
        'offset': offset,
      });
      final videos = (response.data['videos'] as List)
          .map((e) => Video.fromJson(e as Map<String, dynamic>))
          .toList();
      return FeedPage(videos: videos, total: response.data['total'] as int?);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load feed'));
    }
  }

  Future<bool> toggleLike(String videoId) async {
    try {
      final response = await _dio.post('/api/videos/$videoId/like');
      return response.data['is_liked'] as bool;
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to like video'));
    }
  }

  Future<bool> toggleBookmark(String videoId) async {
    try {
      final response = await _dio.post('/api/videos/$videoId/bookmark');
      return response.data['is_bookmarked'] as bool;
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to bookmark video'));
    }
  }

  Future<void> trackView(String videoId) async {
    try {
      await _dio.post('/api/videos/$videoId/view');
    } catch (_) {
      // Non-critical: view tracking failures shouldn't interrupt playback
    }
  }

  Future<List<Video>> getBookmarkedVideos({int limit = 20, int offset = 0}) async {
    try {
      final response = await _dio.get('/api/videos/bookmarks', queryParameters: {
        'limit': limit,
        'offset': offset,
      });
      return (response.data['videos'] as List)
          .map((e) => Video.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load bookmarks'));
    }
  }

  Future<CreatorDashboard> getDashboard({int topVideosLimit = 5}) async {
    try {
      final response = await _dio.get('/api/videos/dashboard', queryParameters: {
        'top_videos_limit': topVideosLimit,
      });
      return CreatorDashboard.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load dashboard'));
    }
  }

  Future<List<Video>> searchVideos(String query, {int limit = 20, int offset = 0}) async {
    try {
      final response = await _dio.get('/api/videos/search', queryParameters: {
        'q': query,
        'limit': limit,
        'offset': offset,
      });
      return (response.data['videos'] as List)
          .map((e) => Video.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Search failed'));
    }
  }

  Future<List<Video>> getUserVideos(String userId, {int limit = 50, int offset = 0}) async {
    try {
      final response = await _dio.get('/api/videos/user/$userId/videos', queryParameters: {
        'limit': limit,
        'offset': offset,
      });
      return (response.data['videos'] as List)
          .map((e) => Video.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load your videos'));
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
