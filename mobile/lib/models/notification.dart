class AppNotification {
  final String id;
  final String type;
  final String? actorId;
  final String? relatedVideoId;
  final String title;
  final String? message;
  bool isRead;
  final DateTime createdAt;

  AppNotification({
    required this.id,
    required this.type,
    this.actorId,
    this.relatedVideoId,
    required this.title,
    this.message,
    required this.isRead,
    required this.createdAt,
  });

  factory AppNotification.fromJson(Map<String, dynamic> json) {
    return AppNotification(
      id: json['id'] as String,
      type: json['type'] as String,
      actorId: json['actor_id'] as String?,
      relatedVideoId: json['related_video_id'] as String?,
      title: json['title'] as String,
      message: json['message'] as String?,
      isRead: json['is_read'] as bool,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

class NotificationPreferences {
  final String id;
  bool pushEnabled;
  bool emailEnabled;
  bool inAppEnabled;
  bool followNotifications;
  bool likeNotifications;
  bool commentNotifications;
  bool mentionNotifications;
  bool messageNotifications;
  String emailDigestFrequency;

  NotificationPreferences({
    required this.id,
    required this.pushEnabled,
    required this.emailEnabled,
    required this.inAppEnabled,
    required this.followNotifications,
    required this.likeNotifications,
    required this.commentNotifications,
    required this.mentionNotifications,
    required this.messageNotifications,
    required this.emailDigestFrequency,
  });

  factory NotificationPreferences.fromJson(Map<String, dynamic> json) {
    return NotificationPreferences(
      id: json['id'] as String,
      pushEnabled: json['push_enabled'] as bool,
      emailEnabled: json['email_enabled'] as bool,
      inAppEnabled: json['in_app_enabled'] as bool,
      followNotifications: json['follow_notifications'] as bool,
      likeNotifications: json['like_notifications'] as bool,
      commentNotifications: json['comment_notifications'] as bool,
      mentionNotifications: json['mention_notifications'] as bool,
      messageNotifications: json['message_notifications'] as bool,
      emailDigestFrequency: json['email_digest_frequency'] as String? ?? 'daily',
    );
  }
}
