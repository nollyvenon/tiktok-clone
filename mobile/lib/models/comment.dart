import 'video.dart';

class Comment {
  final String id;
  final String videoId;
  final String userId;
  final VideoAuthor user;
  final String? parentCommentId;
  String content;
  int likesCount;
  int repliesCount;
  bool isPinned;
  bool isLiked;
  final DateTime createdAt;
  DateTime updatedAt;

  Comment({
    required this.id,
    required this.videoId,
    required this.userId,
    required this.user,
    this.parentCommentId,
    required this.content,
    required this.likesCount,
    required this.repliesCount,
    required this.isPinned,
    required this.isLiked,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Comment.fromJson(Map<String, dynamic> json) {
    return Comment(
      id: json['id'] as String,
      videoId: json['video_id'] as String,
      userId: json['user_id'] as String,
      user: VideoAuthor.fromJson(json['user'] as Map<String, dynamic>),
      parentCommentId: json['parent_comment_id'] as String?,
      content: json['content'] as String,
      likesCount: json['likes_count'] as int,
      repliesCount: json['replies_count'] as int,
      isPinned: json['is_pinned'] as bool,
      isLiked: json['is_liked'] as bool? ?? false,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }
}

class CommentPage {
  final List<Comment> comments;
  final int total;
  final int limit;
  final int offset;

  CommentPage({
    required this.comments,
    required this.total,
    required this.limit,
    required this.offset,
  });

  factory CommentPage.fromJson(Map<String, dynamic> json) {
    return CommentPage(
      comments: (json['comments'] as List)
          .map((e) => Comment.fromJson(e as Map<String, dynamic>))
          .toList(),
      total: json['total'] as int,
      limit: json['limit'] as int,
      offset: json['offset'] as int,
    );
  }
}
