class Shop {
  final String id;
  final String userId;
  final String name;
  final String? description;
  final bool isActive;

  Shop({required this.id, required this.userId, required this.name, this.description, required this.isActive});

  factory Shop.fromJson(Map<String, dynamic> json) {
    return Shop(
      id: json['id'] as String,
      userId: json['user_id'] as String,
      name: json['name'] as String,
      description: json['description'] as String?,
      isActive: json['is_active'] as bool,
    );
  }
}

class ShopProduct {
  final String id;
  final String shopId;
  final String name;
  final String? description;
  final int price;
  final int? stockQuantity;
  final bool isActive;

  ShopProduct({
    required this.id,
    required this.shopId,
    required this.name,
    this.description,
    required this.price,
    this.stockQuantity,
    required this.isActive,
  });

  factory ShopProduct.fromJson(Map<String, dynamic> json) {
    return ShopProduct(
      id: json['id'] as String,
      shopId: json['shop_id'] as String,
      name: json['name'] as String,
      description: json['description'] as String?,
      price: json['price'] as int,
      stockQuantity: json['stock_quantity'] as int?,
      isActive: json['is_active'] as bool,
    );
  }
}

class ShopWithProducts {
  final Shop shop;
  final List<ShopProduct> products;

  ShopWithProducts({required this.shop, required this.products});

  factory ShopWithProducts.fromJson(Map<String, dynamic> json) {
    return ShopWithProducts(
      shop: Shop.fromJson(json['shop'] as Map<String, dynamic>),
      products: (json['products'] as List)
          .map((e) => ShopProduct.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

class ShopOrder {
  final String id;
  final String productId;
  final String shopId;
  final String buyerId;
  final int quantity;
  final int totalAmount;
  final String status;

  ShopOrder({
    required this.id,
    required this.productId,
    required this.shopId,
    required this.buyerId,
    required this.quantity,
    required this.totalAmount,
    required this.status,
  });

  factory ShopOrder.fromJson(Map<String, dynamic> json) {
    return ShopOrder(
      id: json['id'] as String,
      productId: json['product_id'] as String,
      shopId: json['shop_id'] as String,
      buyerId: json['buyer_id'] as String,
      quantity: json['quantity'] as int,
      totalAmount: json['total_amount'] as int,
      status: json['status'] as String,
    );
  }
}
