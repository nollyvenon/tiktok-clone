class LiveStream {
  final String id;
  final String creatorId;
  final String title;
  final String status;
  final int viewerCount;
  final int peakViewerCount;

  LiveStream({
    required this.id,
    required this.creatorId,
    required this.title,
    required this.status,
    required this.viewerCount,
    required this.peakViewerCount,
  });

  factory LiveStream.fromJson(Map<String, dynamic> json) {
    return LiveStream(
      id: json['id'] as String,
      creatorId: json['creator_id'] as String,
      title: json['title'] as String,
      status: json['status'] as String,
      viewerCount: json['viewer_count'] as int,
      peakViewerCount: json['peak_viewer_count'] as int,
    );
  }
}

class LiveChatMessage {
  final String id;
  final String userId;
  final String username;
  final String content;

  LiveChatMessage({required this.id, required this.userId, required this.username, required this.content});

  factory LiveChatMessage.fromJson(Map<String, dynamic> json) {
    return LiveChatMessage(
      id: json['id'] as String,
      userId: json['user_id'] as String,
      username: json['username'] as String,
      content: json['content'] as String,
    );
  }
}
