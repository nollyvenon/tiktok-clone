import 'package:dio/dio.dart';

import '../models/notification.dart';
import 'api_client.dart';
import 'auth_service.dart';

class NotificationsPage {
  final List<AppNotification> notifications;
  final int total;
  final int unreadCount;

  NotificationsPage({required this.notifications, required this.total, required this.unreadCount});
}

class NotificationService {
  final Dio _dio = ApiClient().dio;

  Future<NotificationsPage> getNotifications({int limit = 20, int offset = 0, bool unreadOnly = false}) async {
    try {
      final response = await _dio.get('/api/notifications', queryParameters: {
        'limit': limit,
        'offset': offset,
        'unread_only': unreadOnly,
      });
      final notifications = (response.data['notifications'] as List)
          .map((e) => AppNotification.fromJson(e as Map<String, dynamic>))
          .toList();
      return NotificationsPage(
        notifications: notifications,
        total: response.data['total'] as int,
        unreadCount: response.data['unread_count'] as int,
      );
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load notifications'));
    }
  }

  Future<void> markAsRead(String notificationId) async {
    try {
      await _dio.put('/api/notifications/$notificationId/read');
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to mark notification as read'));
    }
  }

  Future<int> markAllAsRead() async {
    try {
      final response = await _dio.put('/api/notifications/read-all');
      return response.data['count'] as int;
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to mark all as read'));
    }
  }

  Future<void> deleteNotification(String notificationId) async {
    try {
      await _dio.delete('/api/notifications/$notificationId');
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to delete notification'));
    }
  }

  Future<NotificationPreferences> getPreferences() async {
    try {
      final response = await _dio.get('/api/notifications/preferences');
      return NotificationPreferences.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load preferences'));
    }
  }

  Future<NotificationPreferences> updatePreferences(Map<String, dynamic> updates) async {
    try {
      final response = await _dio.put('/api/notifications/preferences', data: updates);
      return NotificationPreferences.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to save preferences'));
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
