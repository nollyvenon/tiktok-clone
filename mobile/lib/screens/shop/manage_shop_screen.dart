import 'package:flutter/material.dart';

import '../../models/shop.dart';
import '../../services/shop_service.dart';
import '../../services/auth_service.dart';

class ManageShopScreen extends StatefulWidget {
  const ManageShopScreen({super.key});

  @override
  State<ManageShopScreen> createState() => _ManageShopScreenState();
}

class _ManageShopScreenState extends State<ManageShopScreen> {
  final _shopService = ShopService();
  final _nameController = TextEditingController();
  final _descController = TextEditingController();
  final _productNameController = TextEditingController();
  final _productPriceController = TextEditingController();
  final _productStockController = TextEditingController();

  Shop? _shop;
  List<ShopProduct> _products = [];
  List<ShopOrder> _receivedOrders = [];
  bool _isLoading = true;
  String? _error;
  String? _productError;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _descController.dispose();
    _productNameController.dispose();
    _productPriceController.dispose();
    _productStockController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _isLoading = true);
    try {
      final shop = await _shopService.getMyShop();
      if (shop != null) {
        final withProducts = await _shopService.getShop(shop.id);
        final orders = await _shopService.getReceivedOrders();
        if (!mounted) return;
        setState(() {
          _shop = shop;
          _products = withProducts.products;
          _receivedOrders = orders;
          _nameController.text = shop.name;
          _descController.text = shop.description ?? '';
        });
      } else if (mounted) {
        setState(() => _shop = null);
      }
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _saveShop() async {
    if (_nameController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Shop name is required')));
      return;
    }
    try {
      await _shopService.upsertMyShop(_nameController.text, description: _descController.text);
      await _load();
    } on ApiException catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  Future<void> _addProduct() async {
    setState(() => _productError = null);
    try {
      final price = (double.tryParse(_productPriceController.text) ?? 0) * 100;
      await _shopService.createProduct(
        name: _productNameController.text,
        price: price.round(),
        stockQuantity: _productStockController.text.isEmpty ? null : int.tryParse(_productStockController.text),
      );
      _productNameController.clear();
      _productPriceController.clear();
      _productStockController.clear();
      await _load();
    } on ApiException catch (e) {
      setState(() => _productError = e.message);
    }
  }

  Future<void> _deleteProduct(String productId) async {
    try {
      await _shopService.deleteProduct(productId);
      await _load();
    } on ApiException catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  Future<void> _fulfillOrder(String orderId) async {
    try {
      await _shopService.fulfillOrder(orderId);
      await _load();
    } on ApiException catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  Future<void> _cancelOrder(String orderId) async {
    try {
      await _shopService.cancelOrder(orderId);
      await _load();
    } on ApiException catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Manage Shop')),
      body: RefreshIndicator(
        onRefresh: _load,
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
                ? Center(child: Text(_error!))
                : _buildContent(),
      ),
    );
  }

  Widget _buildContent() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text('Shop details', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        const SizedBox(height: 8),
        TextField(
          controller: _nameController,
          decoration: const InputDecoration(labelText: 'Shop name', border: OutlineInputBorder()),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _descController,
          decoration: const InputDecoration(labelText: 'Description', border: OutlineInputBorder()),
        ),
        const SizedBox(height: 8),
        ElevatedButton(
          onPressed: _saveShop,
          child: Text(_shop == null ? 'Create shop' : 'Save changes'),
        ),
        if (_shop != null) ...[
          const SizedBox(height: 24),
          const Text('Products', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 8),
          TextField(
            controller: _productNameController,
            decoration: const InputDecoration(labelText: 'Product name', border: OutlineInputBorder()),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _productPriceController,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'Price (\$)', border: OutlineInputBorder()),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _productStockController,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'Stock (blank = unlimited)', border: OutlineInputBorder()),
          ),
          if (_productError != null) ...[
            const SizedBox(height: 8),
            Text(_productError!, style: const TextStyle(color: Colors.red)),
          ],
          const SizedBox(height: 8),
          ElevatedButton(onPressed: _addProduct, child: const Text('Add product')),
          const SizedBox(height: 12),
          if (_products.isEmpty)
            const Text('No products yet.', style: TextStyle(color: Colors.grey))
          else
            ..._products.map((product) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text(product.name),
                  subtitle: Text(
                    '\$${(product.price / 100).toStringAsFixed(2)} · ${product.stockQuantity == null ? 'Unlimited' : '${product.stockQuantity} in stock'}',
                  ),
                  trailing: IconButton(
                    icon: const Icon(Icons.delete, color: Colors.red),
                    onPressed: () => _deleteProduct(product.id),
                  ),
                )),
          const SizedBox(height: 24),
          const Text('Received orders', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 8),
          if (_receivedOrders.isEmpty)
            const Text('No orders yet.', style: TextStyle(color: Colors.grey))
          else
            ..._receivedOrders.map((order) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text('Qty ${order.quantity} · \$${(order.totalAmount / 100).toStringAsFixed(2)}'),
                  subtitle: Text(order.status),
                  trailing: order.status == 'pending'
                      ? Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            TextButton(onPressed: () => _fulfillOrder(order.id), child: const Text('Fulfill')),
                            TextButton(
                              onPressed: () => _cancelOrder(order.id),
                              child: const Text('Cancel', style: TextStyle(color: Colors.red)),
                            ),
                          ],
                        )
                      : null,
                )),
        ],
      ],
    );
  }
}
