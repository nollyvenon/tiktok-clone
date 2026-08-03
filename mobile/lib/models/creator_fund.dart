class FundingProgram {
  final String id;
  final String name;
  final String? description;
  final int minFollowers;
  final int minPublishedVideos;
  final int minTotalViews;
  final int awardAmount;
  final bool isActive;

  FundingProgram({
    required this.id,
    required this.name,
    this.description,
    required this.minFollowers,
    required this.minPublishedVideos,
    required this.minTotalViews,
    required this.awardAmount,
    required this.isActive,
  });

  factory FundingProgram.fromJson(Map<String, dynamic> json) {
    return FundingProgram(
      id: json['id'] as String,
      name: json['name'] as String,
      description: json['description'] as String?,
      minFollowers: json['min_followers'] as int,
      minPublishedVideos: json['min_published_videos'] as int,
      minTotalViews: json['min_total_views'] as int,
      awardAmount: json['award_amount'] as int,
      isActive: json['is_active'] as bool,
    );
  }
}

class CreatorApplication {
  final String id;
  final String programId;
  final String userId;
  final int followersCount;
  final int publishedVideosCount;
  final int totalViewsCount;
  final bool meetsRequirements;
  final String status;
  final String? decisionReason;
  final int? awardedAmount;

  CreatorApplication({
    required this.id,
    required this.programId,
    required this.userId,
    required this.followersCount,
    required this.publishedVideosCount,
    required this.totalViewsCount,
    required this.meetsRequirements,
    required this.status,
    this.decisionReason,
    this.awardedAmount,
  });

  factory CreatorApplication.fromJson(Map<String, dynamic> json) {
    return CreatorApplication(
      id: json['id'] as String,
      programId: json['program_id'] as String,
      userId: json['user_id'] as String,
      followersCount: json['followers_count'] as int,
      publishedVideosCount: json['published_videos_count'] as int,
      totalViewsCount: json['total_views_count'] as int,
      meetsRequirements: json['meets_requirements'] as bool,
      status: json['status'] as String,
      decisionReason: json['decision_reason'] as String?,
      awardedAmount: json['awarded_amount'] as int?,
    );
  }
}
