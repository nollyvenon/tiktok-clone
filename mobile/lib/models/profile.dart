import 'user.dart';

class ProfileStatistics {
  final int followersCount;
  final int followingCount;
  final int videosCount;
  final int likesCount;
  final int totalViews;

  ProfileStatistics({
    required this.followersCount,
    required this.followingCount,
    required this.videosCount,
    required this.likesCount,
    required this.totalViews,
  });

  factory ProfileStatistics.fromJson(Map<String, dynamic> json) {
    return ProfileStatistics(
      followersCount: json['followers_count'] as int? ?? 0,
      followingCount: json['following_count'] as int? ?? 0,
      videosCount: json['videos_count'] as int? ?? 0,
      likesCount: json['likes_count'] as int? ?? 0,
      totalViews: json['total_views'] as int? ?? 0,
    );
  }
}

class ProfileDetail {
  final User user;
  final ProfileStatistics statistics;
  final bool isFollowing;
  final bool isBlocked;

  ProfileDetail({
    required this.user,
    required this.statistics,
    required this.isFollowing,
    required this.isBlocked,
  });

  factory ProfileDetail.fromJson(Map<String, dynamic> json) {
    return ProfileDetail(
      user: User.fromJson(json['user'] as Map<String, dynamic>),
      statistics: ProfileStatistics.fromJson(json['statistics'] as Map<String, dynamic>),
      isFollowing: json['is_following'] as bool? ?? false,
      isBlocked: json['is_blocked'] as bool? ?? false,
    );
  }
}
