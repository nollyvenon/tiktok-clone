import 'package:flutter/material.dart';

import '../../models/shop.dart';
import '../../services/shop_service.dart';
import '../../services/auth_service.dart';

class ShopScreen extends StatefulWidget {
  final String shopId;

  const ShopScreen({super.key, required this.shopId});

  @override
  State<ShopScreen> createState() => _ShopScreenState();
}

class _ShopScreenState extends State<ShopScreen> {
  final _shopService = ShopService();
  ShopWithProducts? _data;
  bool _isLoading = true;
  String? _error;
  final Set<String> _orderedProductIds = {};

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final data = await _shopService.getShop(widget.shopId);
      if (!mounted) return;
      setState(() => _data = data);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _order(ShopProduct product) async {
    try {
      await _shopService.orderProduct(product.id);
      if (!mounted) return;
      setState(() => _orderedProductIds.add(product.id));
    } on ApiException catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(_data?.shop.name ?? 'Shop')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : RefreshIndicator(onRefresh: _load, child: _buildContent()),
    );
  }

  Widget _buildContent() {
    final data = _data!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (data.shop.description != null && data.shop.description!.isNotEmpty) ...[
          Text(data.shop.description!, style: const TextStyle(color: Colors.grey)),
          const SizedBox(height: 16),
        ],
        if (data.products.isEmpty)
          const Text('No products available yet.', style: TextStyle(color: Colors.grey))
        else
          ...data.products.map((product) {
            final isOrdered = _orderedProductIds.contains(product.id);
            final outOfStock = product.stockQuantity == 0;
            return Container(
              margin: const EdgeInsets.only(bottom: 12),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                border: Border.all(color: Colors.grey.shade300),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(product.name, style: const TextStyle(fontWeight: FontWeight.bold)),
                  if (product.description != null && product.description!.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Text(product.description!, style: const TextStyle(color: Colors.grey)),
                  ],
                  const SizedBox(height: 8),
                  Text('\$${(product.price / 100).toStringAsFixed(2)}', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  Text(
                    product.stockQuantity == null
                        ? 'In stock'
                        : outOfStock
                            ? 'Out of stock'
                            : '${product.stockQuantity} left',
                    style: const TextStyle(fontSize: 12, color: Colors.grey),
                  ),
                  const SizedBox(height: 8),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: isOrdered || outOfStock ? null : () => _order(product),
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.pink, foregroundColor: Colors.white),
                      child: Text(isOrdered ? 'Ordered' : 'Order'),
                    ),
                  ),
                ],
              ),
            );
          }),
      ],
    );
  }
}
