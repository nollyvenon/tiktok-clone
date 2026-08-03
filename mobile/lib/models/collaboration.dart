class CollaboratorSplit {
  final String id;
  final String userId;
  final double revenueSplitPercent;
  final bool isInitiator;
  final String status;

  CollaboratorSplit({
    required this.id,
    required this.userId,
    required this.revenueSplitPercent,
    required this.isInitiator,
    required this.status,
  });

  factory CollaboratorSplit.fromJson(Map<String, dynamic> json) {
    return CollaboratorSplit(
      id: json['id'] as String,
      userId: json['user_id'] as String,
      revenueSplitPercent: (json['revenue_split_percent'] as num).toDouble(),
      isInitiator: json['is_initiator'] as bool,
      status: json['status'] as String,
    );
  }
}

class Collaboration {
  final String id;
  final String videoId;
  final String initiatorId;
  final String? title;
  final String status;
  final List<CollaboratorSplit> collaborators;

  Collaboration({
    required this.id,
    required this.videoId,
    required this.initiatorId,
    this.title,
    required this.status,
    required this.collaborators,
  });

  factory Collaboration.fromJson(Map<String, dynamic> json) {
    return Collaboration(
      id: json['id'] as String,
      videoId: json['video_id'] as String,
      initiatorId: json['initiator_id'] as String,
      title: json['title'] as String?,
      status: json['status'] as String,
      collaborators: (json['collaborators'] as List)
          .map((e) => CollaboratorSplit.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}
