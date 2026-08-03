import 'package:dio/dio.dart';

import '../models/shop.dart';
import 'api_client.dart';
import 'auth_service.dart';

class ShopService {
  final Dio _dio = ApiClient().dio;

  Future<Shop> upsertMyShop(String name, {String? description}) async {
    try {
      final response = await _dio.post('/api/shop/me', data: {
        'name': name,
        if (description != null) 'description': description,
      });
      return Shop.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to save shop'));
    }
  }

  Future<Shop?> getMyShop() async {
    try {
      final response = await _dio.get('/api/shop/me');
      return Shop.fromJson(response.data);
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return null;
      throw ApiException(_extractError(e, 'Failed to load shop'));
    }
  }

  Future<ShopWithProducts> getShop(String shopId) async {
    try {
      final response = await _dio.get('/api/shop/$shopId');
      return ShopWithProducts.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Shop not found'));
    }
  }

  Future<ShopWithProducts?> getShopByUser(String userId) async {
    try {
      final response = await _dio.get('/api/shop/user/$userId');
      return ShopWithProducts.fromJson(response.data);
    } on DioException catch (e) {
      if (e.response?.statusCode == 400) return null;
      throw ApiException(_extractError(e, 'Failed to load shop'));
    }
  }

  Future<ShopProduct> createProduct({
    required String name,
    String? description,
    required int price,
    int? stockQuantity,
  }) async {
    try {
      final response = await _dio.post('/api/shop/products', data: {
        'name': name,
        if (description != null) 'description': description,
        'price': price,
        'stock_quantity': stockQuantity,
      });
      return ShopProduct.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to add product'));
    }
  }

  Future<void> deleteProduct(String productId) async {
    try {
      await _dio.delete('/api/shop/products/$productId');
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to delete product'));
    }
  }

  Future<ShopOrder> orderProduct(String productId, {int quantity = 1}) async {
    try {
      final response = await _dio.post('/api/shop/products/$productId/order', data: {
        'quantity': quantity,
      });
      return ShopOrder.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to place order'));
    }
  }

  Future<List<ShopOrder>> getMyOrders() async {
    try {
      final response = await _dio.get('/api/shop/orders/me');
      return (response.data['orders'] as List)
          .map((e) => ShopOrder.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load your orders'));
    }
  }

  Future<List<ShopOrder>> getReceivedOrders() async {
    try {
      final response = await _dio.get('/api/shop/orders/received');
      return (response.data['orders'] as List)
          .map((e) => ShopOrder.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to load received orders'));
    }
  }

  Future<ShopOrder> fulfillOrder(String orderId) async {
    try {
      final response = await _dio.post('/api/shop/orders/$orderId/fulfill');
      return ShopOrder.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to fulfill order'));
    }
  }

  Future<ShopOrder> cancelOrder(String orderId) async {
    try {
      final response = await _dio.post('/api/shop/orders/$orderId/cancel');
      return ShopOrder.fromJson(response.data);
    } on DioException catch (e) {
      throw ApiException(_extractError(e, 'Failed to cancel order'));
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
