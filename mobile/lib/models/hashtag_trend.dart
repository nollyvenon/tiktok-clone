class HashtagTrend {
  final String id;
  final String hashtag;
  final int usageCount;
  final int uniqueCreators;
  final int popularityScore;
  final double trendVelocity;

  HashtagTrend({
    required this.id,
    required this.hashtag,
    required this.usageCount,
    required this.uniqueCreators,
    required this.popularityScore,
    required this.trendVelocity,
  });

  factory HashtagTrend.fromJson(Map<String, dynamic> json) {
    return HashtagTrend(
      id: json['id'] as String,
      hashtag: json['hashtag'] as String,
      usageCount: json['usage_count'] as int,
      uniqueCreators: json['unique_creators'] as int,
      popularityScore: json['popularity_score'] as int,
      trendVelocity: (json['trend_velocity'] as num).toDouble(),
    );
  }
}

class Challenge {
  final String id;
  final String hashtag;
  final String title;
  final String? description;
  final int? prizePool;
  final int participationCount;
  final bool isActive;

  Challenge({
    required this.id,
    required this.hashtag,
    required this.title,
    this.description,
    this.prizePool,
    required this.participationCount,
    required this.isActive,
  });

  factory Challenge.fromJson(Map<String, dynamic> json) {
    return Challenge(
      id: json['id'] as String,
      hashtag: json['hashtag'] as String,
      title: json['title'] as String,
      description: json['description'] as String?,
      prizePool: json['prize_pool'] as int?,
      participationCount: json['participation_count'] as int,
      isActive: json['is_active'] as bool? ?? true,
    );
  }
}
