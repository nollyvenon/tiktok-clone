class Draft {
  final String id;
  final String? uploadId;
  final String? title;
  final String? description;
  final String? hashtags;
  final String? thumbnailUrl;
  final bool isPublic;
  final String status;
  final DateTime? scheduledPublishAt;
  final DateTime createdAt;

  Draft({
    required this.id,
    this.uploadId,
    this.title,
    this.description,
    this.hashtags,
    this.thumbnailUrl,
    required this.isPublic,
    required this.status,
    this.scheduledPublishAt,
    required this.createdAt,
  });

  factory Draft.fromJson(Map<String, dynamic> json) {
    return Draft(
      id: json['id'] as String,
      uploadId: json['upload_id'] as String?,
      title: json['title'] as String?,
      description: json['description'] as String?,
      hashtags: json['hashtags'] as String?,
      thumbnailUrl: json['thumbnail_url'] as String?,
      isPublic: json['is_public'] as bool? ?? true,
      status: json['status'] as String,
      scheduledPublishAt: json['scheduled_publish_at'] != null
          ? DateTime.parse(json['scheduled_publish_at'] as String)
          : null,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}
