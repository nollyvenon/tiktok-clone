import 'package:dio/dio.dart';

import '../models/creator_fund.dart';
import 'api_client.dart';
import 'auth_service.dart';

class CreatorFundService {
  final Dio _dio = ApiClient().dio;

  Future<List<FundingProgram>> listPrograms() async {
    try {
      final response = await _dio.get('/api/creator-fund/programs');
      return (response.data['programs'] as List)
          .map((e) => FundingProgram.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load funding programs'));
    }
  }

  Future<CreatorApplication> applyToProgram(String programId) async {
    try {
      final response = await _dio.post('/api/creator-fund/programs/$programId/apply');
      return CreatorApplication.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to apply'));
    }
  }

  Future<List<CreatorApplication>> getMyApplications() async {
    try {
      final response = await _dio.get('/api/creator-fund/me/applications');
      return (response.data as List)
          .map((e) => CreatorApplication.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load your applications'));
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
