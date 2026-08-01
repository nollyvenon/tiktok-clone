class VideoAuthor {
  final String id;
  final String username;
  final String? avatarUrl;
  final bool isVerified;
  final bool isCreator;

  VideoAuthor({
    required this.id,
    required this.username,
    this.avatarUrl,
    required this.isVerified,
    required this.isCreator,
  });

  factory VideoAuthor.fromJson(Map<String, dynamic> json) {
    return VideoAuthor(
      id: json['id'] as String,
      username: json['username'] as String,
      avatarUrl: json['avatar_url'] as String?,
      isVerified: json['is_verified'] as bool? ?? false,
      isCreator: json['is_creator'] as bool? ?? false,
    );
  }
}

class Video {
  final String id;
  final String userId;
  final VideoAuthor author;
  final String? title;
  final String? description;
  final String videoUrl;
  final String? thumbnailUrl;
  final int? duration;
  final String? hashtags;
  final bool isPublic;
  final int viewsCount;
  int likesCount;
  final int commentsCount;
  final int sharesCount;
  int bookmarksCount;
  bool isLiked;
  bool isBookmarked;
  final bool allowComments;

  Video({
    required this.id,
    required this.userId,
    required this.author,
    this.title,
    this.description,
    required this.videoUrl,
    this.thumbnailUrl,
    this.duration,
    this.hashtags,
    required this.isPublic,
    required this.viewsCount,
    required this.likesCount,
    required this.commentsCount,
    required this.sharesCount,
    required this.bookmarksCount,
    required this.isLiked,
    required this.isBookmarked,
    required this.allowComments,
  });

  factory Video.fromJson(Map<String, dynamic> json) {
    return Video(
      id: json['id'] as String,
      userId: json['user_id'] as String,
      author: VideoAuthor.fromJson(json['user'] as Map<String, dynamic>),
      title: json['title'] as String?,
      description: json['description'] as String?,
      videoUrl: json['video_url'] as String,
      thumbnailUrl: json['thumbnail_url'] as String?,
      duration: json['duration'] as int?,
      hashtags: json['hashtags'] as String?,
      isPublic: json['is_public'] as bool? ?? true,
      viewsCount: json['views_count'] as int? ?? 0,
      likesCount: json['likes_count'] as int? ?? 0,
      commentsCount: json['comments_count'] as int? ?? 0,
      sharesCount: json['shares_count'] as int? ?? 0,
      bookmarksCount: json['bookmarks_count'] as int? ?? 0,
      isLiked: json['is_liked'] as bool? ?? false,
      isBookmarked: json['is_bookmarked'] as bool? ?? false,
      allowComments: json['allow_comments'] as bool? ?? true,
    );
  }

  List<String> get hashtagList =>
      (hashtags ?? '').split(',').map((t) => t.trim()).where((t) => t.isNotEmpty).toList();
}
