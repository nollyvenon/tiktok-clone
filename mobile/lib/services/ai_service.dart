import 'package:dio/dio.dart';

import 'api_client.dart';
import 'auth_service.dart';

class AICreditsInfo {
  final int totalCredits;
  final int availableCredits;
  final int usedCredits;
  final int monthlyLimit;

  AICreditsInfo({
    required this.totalCredits,
    required this.availableCredits,
    required this.usedCredits,
    required this.monthlyLimit,
  });

  factory AICreditsInfo.fromJson(Map<String, dynamic> json) {
    return AICreditsInfo(
      totalCredits: json['total_credits'] as int,
      availableCredits: json['available_credits'] as int,
      usedCredits: json['used_credits'] as int,
      monthlyLimit: json['monthly_limit'] as int,
    );
  }
}

class SoundRecommendation {
  final String id;
  final String soundTitle;
  final String? artist;
  final String category;
  final bool isTrending;

  SoundRecommendation({
    required this.id,
    required this.soundTitle,
    this.artist,
    required this.category,
    required this.isTrending,
  });

  factory SoundRecommendation.fromJson(Map<String, dynamic> json) {
    return SoundRecommendation(
      id: json['id'] as String,
      soundTitle: json['sound_title'] as String,
      artist: json['artist'] as String?,
      category: json['category'] as String,
      isTrending: json['is_trending'] as bool? ?? false,
    );
  }
}

class AIService {
  final Dio _dio = ApiClient().dio;

  Future<AICreditsInfo> getCredits() async {
    try {
      final response = await _dio.get('/api/ai/credits');
      return AICreditsInfo.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load AI credits'));
    }
  }

  Future<void> removeBackground(String segmentId, {String mode = 'blur', int blurLevel = 5}) async {
    try {
      await _dio.post('/api/ai/background-removal', data: {
        'segment_id': segmentId,
        'mode': mode,
        'blur_level': blurLevel,
      });
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Background removal failed'));
    }
  }

  Future<void> generateCaptions(String segmentId, {String language = 'en'}) async {
    try {
      await _dio.post('/api/ai/captions', data: {
        'segment_id': segmentId,
        'language': language,
      });
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Caption generation failed'));
    }
  }

  Future<void> applyColorCorrection(String segmentId, {String method = 'auto_enhance'}) async {
    try {
      await _dio.post('/api/ai/color-correction', data: {
        'segment_id': segmentId,
        'method': method,
      });
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Color correction failed'));
    }
  }

  Future<void> getFrameSuggestions(String segmentId, {String targetAspectRatio = '9:16'}) async {
    try {
      await _dio.post('/api/ai/smart-frame', queryParameters: {
        'segment_id': segmentId,
        'target_aspect_ratio': targetAspectRatio,
      });
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Smart framing failed'));
    }
  }

  Future<void> generateVoiceover(String segmentId, String text, String voiceId) async {
    try {
      await _dio.post('/api/ai/voiceover', data: {
        'segment_id': segmentId,
        'text': text,
        'voice_id': voiceId,
      });
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Voiceover generation failed'));
    }
  }

  Future<List<SoundRecommendation>> getSoundRecommendations({String? category}) async {
    try {
      final response = await _dio.get('/api/ai/sounds/recommendations', queryParameters: {
        if (category != null) 'category': category,
      });
      return (response.data['sounds'] as List)
          .map((e) => SoundRecommendation.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load sound recommendations'));
    }
  }

  String _extractError(DioException e, String fallback) {
    final data = e.response?.data;
    if (data is Map && data['detail'] != null) {
      return data['detail'].toString();
    }
    return fallback;
  }
}
