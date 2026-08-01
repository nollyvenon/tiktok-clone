class EditorSegment {
  final String id;
  final int startTime;
  final int endTime;
  final int order;
  final String contentType;
  final String contentUrl;
  List<String> effects;
  int volume;
  bool muted;

  EditorSegment({
    required this.id,
    required this.startTime,
    required this.endTime,
    required this.order,
    required this.contentType,
    required this.contentUrl,
    required this.effects,
    required this.volume,
    required this.muted,
  });

  factory EditorSegment.fromJson(Map<String, dynamic> json) {
    return EditorSegment(
      id: json['id'] as String,
      startTime: json['start_time'] as int,
      endTime: json['end_time'] as int,
      order: json['order'] as int,
      contentType: json['content_type'] as String,
      contentUrl: json['content_url'] as String,
      effects: (json['effects'] as List?)?.map((e) => e as String).toList() ?? [],
      volume: json['volume'] as int,
      muted: json['muted'] as bool,
    );
  }
}

class EditorStateData {
  final String draftId;
  final List<EditorSegment> segments;
  final int totalDuration;
  final int textOverlayCount;

  EditorStateData({
    required this.draftId,
    required this.segments,
    required this.totalDuration,
    required this.textOverlayCount,
  });

  factory EditorStateData.fromJson(Map<String, dynamic> json) {
    return EditorStateData(
      draftId: json['draft_id'] as String,
      segments: (json['segments'] as List)
          .map((e) => EditorSegment.fromJson(e as Map<String, dynamic>))
          .toList(),
      totalDuration: json['total_duration'] as int,
      textOverlayCount: (json['text_overlays'] as List).length,
    );
  }
}
