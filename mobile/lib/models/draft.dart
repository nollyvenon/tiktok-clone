class Draft {
  final String id;
  final String? uploadId;
  final String? title;
  final String? description;
  final String? hashtags;
  final String? thumbnailUrl;
  final bool isPublic;
  final bool allowComments;
  final bool allowDuets;
  final bool allowStitches;
  final String? originalVideoId;
  final String? remixType;
  final String? musicId;
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
    this.allowComments = true,
    this.allowDuets = true,
    this.allowStitches = true,
    this.originalVideoId,
    this.remixType,
    this.musicId,
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
      allowComments: json['allow_comments'] as bool? ?? true,
      allowDuets: json['allow_duets'] as bool? ?? true,
      allowStitches: json['allow_stitches'] as bool? ?? true,
      originalVideoId: json['original_video_id'] as String?,
      remixType: json['remix_type'] as String?,
      musicId: json['music_id'] as String?,
      status: json['status'] as String,
      scheduledPublishAt: json['scheduled_publish_at'] != null
          ? DateTime.parse(json['scheduled_publish_at'] as String)
          : null,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  Draft copyWith({String? musicId}) {
    return Draft(
      id: id,
      uploadId: uploadId,
      title: title,
      description: description,
      hashtags: hashtags,
      thumbnailUrl: thumbnailUrl,
      isPublic: isPublic,
      allowComments: allowComments,
      allowDuets: allowDuets,
      allowStitches: allowStitches,
      originalVideoId: originalVideoId,
      remixType: remixType,
      musicId: musicId ?? this.musicId,
      status: status,
      scheduledPublishAt: scheduledPublishAt,
      createdAt: createdAt,
    );
  }

  Map<String, dynamic> toUpdateJson() {
    return {
      'title': title,
      'description': description,
      'hashtags': hashtags,
      'thumbnail_url': thumbnailUrl,
      'is_public': isPublic,
      'allow_comments': allowComments,
      'allow_duets': allowDuets,
      'allow_stitches': allowStitches,
      'original_video_id': originalVideoId,
      'remix_type': remixType,
      'music_id': musicId,
    };
  }
}
