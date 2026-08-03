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

class FilterPreset {
  final String id;
  final String name;
  final String label;
  final int brightness;
  final int contrast;
  final int saturation;
  final int hue;
  final int temperature;

  FilterPreset({
    required this.id,
    required this.name,
    required this.label,
    required this.brightness,
    required this.contrast,
    required this.saturation,
    required this.hue,
    required this.temperature,
  });

  factory FilterPreset.fromJson(Map<String, dynamic> json) {
    return FilterPreset(
      id: json['id'] as String,
      name: json['name'] as String,
      label: json['label'] as String,
      brightness: json['brightness'] as int,
      contrast: json['contrast'] as int,
      saturation: json['saturation'] as int,
      hue: json['hue'] as int,
      temperature: json['temperature'] as int,
    );
  }
}

class AIAgent {
  final String id;
  final String name;
  final String label;
  final String? description;

  AIAgent({required this.id, required this.name, required this.label, this.description});

  factory AIAgent.fromJson(Map<String, dynamic> json) {
    return AIAgent(
      id: json['id'] as String,
      name: json['name'] as String,
      label: json['label'] as String,
      description: json['description'] as String?,
    );
  }
}

class AgentStepResult {
  final String operation;
  final String status;
  final int creditsUsed;
  final String? error;

  AgentStepResult({required this.operation, required this.status, required this.creditsUsed, this.error});

  factory AgentStepResult.fromJson(Map<String, dynamic> json) {
    return AgentStepResult(
      operation: json['operation'] as String,
      status: json['status'] as String,
      creditsUsed: json['credits_used'] as int? ?? 0,
      error: json['error'] as String?,
    );
  }
}

class AgentExecution {
  final String id;
  final String agentId;
  final String status;
  final List<AgentStepResult> stepsLog;
  final int totalCreditsUsed;
  final String? errorMessage;

  AgentExecution({
    required this.id,
    required this.agentId,
    required this.status,
    required this.stepsLog,
    required this.totalCreditsUsed,
    this.errorMessage,
  });

  factory AgentExecution.fromJson(Map<String, dynamic> json) {
    return AgentExecution(
      id: json['id'] as String,
      agentId: json['agent_id'] as String,
      status: json['status'] as String,
      stepsLog: (json['steps_log'] as List)
          .map((e) => AgentStepResult.fromJson(e as Map<String, dynamic>))
          .toList(),
      totalCreditsUsed: json['total_credits_used'] as int,
      errorMessage: json['error_message'] as String?,
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

  Future<void> applyColorCorrection(
    String segmentId, {
    String method = 'auto_enhance',
    String? presetName,
    int? brightness,
    int? contrast,
    int? saturation,
    int? hue,
    int? temperature,
  }) async {
    try {
      await _dio.post('/api/ai/color-correction', data: {
        'segment_id': segmentId,
        'method': method,
        if (presetName != null) 'preset_name': presetName,
        if (brightness != null) 'brightness': brightness,
        if (contrast != null) 'contrast': contrast,
        if (saturation != null) 'saturation': saturation,
        if (hue != null) 'hue': hue,
        if (temperature != null) 'temperature': temperature,
      });
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Color correction failed'));
    }
  }

  Future<List<FilterPreset>> getFilterPresets() async {
    try {
      final response = await _dio.get('/api/ai/filters/presets');
      return (response.data['presets'] as List)
          .map((e) => FilterPreset.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load filter presets'));
    }
  }

  Future<List<AIAgent>> getAgents() async {
    try {
      final response = await _dio.get('/api/ai/agents');
      return (response.data['agents'] as List)
          .map((e) => AIAgent.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load AI agents'));
    }
  }

  Future<AgentExecution> executeAgent(String agentId, String segmentId) async {
    try {
      final response = await _dio.post(
        '/api/ai/agents/$agentId/execute',
        queryParameters: {'segment_id': segmentId},
      );
      return AgentExecution.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to run agent'));
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
