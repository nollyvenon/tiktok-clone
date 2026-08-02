class TopVideoSummary {
  final String videoId;
  final String? title;
  final String? thumbnailUrl;
  final int views;
  final int likes;
  final int comments;
  final double engagementRate;

  TopVideoSummary({
    required this.videoId,
    this.title,
    this.thumbnailUrl,
    required this.views,
    required this.likes,
    required this.comments,
    required this.engagementRate,
  });

  factory TopVideoSummary.fromJson(Map<String, dynamic> json) {
    return TopVideoSummary(
      videoId: json['video_id'] as String,
      title: json['title'] as String?,
      thumbnailUrl: json['thumbnail_url'] as String?,
      views: json['views'] as int,
      likes: json['likes'] as int,
      comments: json['comments'] as int,
      engagementRate: (json['engagement_rate'] as num).toDouble(),
    );
  }
}

class CreatorDashboard {
  final int videoCount;
  final int totalViews;
  final int totalLikes;
  final int totalComments;
  final int totalShares;
  final int totalBookmarks;
  final double averageEngagementRate;
  final int followersCount;
  final List<TopVideoSummary> topVideos;

  CreatorDashboard({
    required this.videoCount,
    required this.totalViews,
    required this.totalLikes,
    required this.totalComments,
    required this.totalShares,
    required this.totalBookmarks,
    required this.averageEngagementRate,
    required this.followersCount,
    required this.topVideos,
  });

  factory CreatorDashboard.fromJson(Map<String, dynamic> json) {
    return CreatorDashboard(
      videoCount: json['video_count'] as int,
      totalViews: json['total_views'] as int,
      totalLikes: json['total_likes'] as int,
      totalComments: json['total_comments'] as int,
      totalShares: json['total_shares'] as int,
      totalBookmarks: json['total_bookmarks'] as int,
      averageEngagementRate: (json['average_engagement_rate'] as num).toDouble(),
      followersCount: json['followers_count'] as int,
      topVideos: (json['top_videos'] as List)
          .map((e) => TopVideoSummary.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}
