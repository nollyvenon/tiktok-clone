import 'package:dio/dio.dart';

import '../models/monetization.dart';
import 'api_client.dart';
import 'auth_service.dart';

class MonetizationService {
  final Dio _dio = ApiClient().dio;

  Future<EarningsSummary> getSummary() async {
    try {
      final response = await _dio.get('/api/monetization/summary');
      return EarningsSummary.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load earnings'));
    }
  }

  Future<Payout> requestPayout(int amount) async {
    try {
      final response = await _dio.post('/api/monetization/payouts', data: {'amount': amount});
      return Payout.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to request payout'));
    }
  }

  Future<List<Payout>> getMyPayouts() async {
    try {
      final response = await _dio.get('/api/monetization/payouts/me');
      return (response.data as List).map((e) => Payout.fromJson(e as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load your payouts'));
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
