'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { shopApi } from '@/lib/api';
import { Loader2, Store, Package, Trash2 } from 'lucide-react';

export default function ManageShopPage() {
  const queryClient = useQueryClient();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [productName, setProductName] = useState('');
  const [productPrice, setProductPrice] = useState('');
  const [productStock, setProductStock] = useState('');
  const [productError, setProductError] = useState<string | null>(null);

  const { data: shop, isLoading: shopLoading } = useQuery(
    ['my-shop'],
    () => shopApi.getMyShop(),
    { retry: false, onSuccess: (s) => { setName(s.name); setDescription(s.description || ''); } }
  );

  const { data: shopWithProducts } = useQuery(
    ['my-shop-products', shop?.id],
    () => shopApi.getShop(shop!.id),
    { enabled: !!shop }
  );

  const { data: receivedOrders } = useQuery(
    ['received-orders'],
    () => shopApi.getReceivedOrders(),
    { enabled: !!shop }
  );

  const upsertShopMutation = useMutation(
    () => shopApi.upsertMyShop(name, description || undefined),
    { onSuccess: () => queryClient.invalidateQueries(['my-shop']) }
  );

  const createProductMutation = useMutation(
    () =>
      shopApi.createProduct({
        name: productName,
        price: Math.round(Number(productPrice) * 100),
        stock_quantity: productStock ? Number(productStock) : null,
      }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['my-shop-products']);
        setProductName('');
        setProductPrice('');
        setProductStock('');
        setProductError(null);
      },
      onError: (err: unknown) => {
        const message =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          'Failed to add product';
        setProductError(message);
      },
    }
  );

  const deleteProductMutation = useMutation((productId: string) => shopApi.deleteProduct(productId), {
    onSuccess: () => queryClient.invalidateQueries(['my-shop-products']),
  });

  const fulfillMutation = useMutation((orderId: string) => shopApi.fulfillOrder(orderId), {
    onSuccess: () => queryClient.invalidateQueries(['received-orders']),
  });

  const cancelMutation = useMutation((orderId: string) => shopApi.cancelOrder(orderId), {
    onSuccess: () => queryClient.invalidateQueries(['received-orders']),
  });

  if (shopLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-3xl mx-auto px-4">
        <h1 className="text-3xl font-bold mb-8 flex items-center gap-2">
          <Store className="w-7 h-7 text-pink-600" />
          Manage Shop
        </h1>

        <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 mb-8">
          <h2 className="font-semibold mb-3">Shop details</h2>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Shop name"
            className="w-full border border-gray-300 dark:border-gray-700 dark:bg-gray-800 rounded-lg px-3 py-2 mb-2 text-sm"
          />
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description"
            className="w-full border border-gray-300 dark:border-gray-700 dark:bg-gray-800 rounded-lg px-3 py-2 mb-2 text-sm"
          />
          <button
            onClick={() => upsertShopMutation.mutate()}
            disabled={!name || upsertShopMutation.isLoading}
            className="bg-pink-600 text-white rounded-full px-4 py-1.5 text-sm font-semibold disabled:opacity-50"
          >
            {shop ? 'Save changes' : 'Create shop'}
          </button>
        </div>

        {shop && (
          <>
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 mb-8">
              <h2 className="font-semibold mb-3 flex items-center gap-2">
                <Package className="w-4 h-4" /> Products
              </h2>
              <div className="grid grid-cols-3 gap-2 mb-2">
                <input
                  value={productName}
                  onChange={(e) => setProductName(e.target.value)}
                  placeholder="Product name"
                  className="border border-gray-300 dark:border-gray-700 dark:bg-gray-800 rounded-lg px-3 py-2 text-sm"
                />
                <input
                  value={productPrice}
                  onChange={(e) => setProductPrice(e.target.value)}
                  placeholder="Price ($)"
                  type="number"
                  className="border border-gray-300 dark:border-gray-700 dark:bg-gray-800 rounded-lg px-3 py-2 text-sm"
                />
                <input
                  value={productStock}
                  onChange={(e) => setProductStock(e.target.value)}
                  placeholder="Stock (blank = unlimited)"
                  type="number"
                  className="border border-gray-300 dark:border-gray-700 dark:bg-gray-800 rounded-lg px-3 py-2 text-sm"
                />
              </div>
              {productError && <p className="text-xs text-red-600 mb-2">{productError}</p>}
              <button
                onClick={() => createProductMutation.mutate()}
                disabled={!productName || !productPrice || createProductMutation.isLoading}
                className="bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded-full px-4 py-1.5 text-sm font-semibold disabled:opacity-50 mb-4"
              >
                Add product
              </button>

              <div className="space-y-2">
                {(shopWithProducts?.products || []).map((product) => (
                  <div
                    key={product.id}
                    className="flex items-center justify-between border-t border-gray-100 dark:border-gray-800 pt-2"
                  >
                    <div>
                      <p className="text-sm font-medium">{product.name}</p>
                      <p className="text-xs text-gray-500">
                        ${(product.price / 100).toFixed(2)} ·{' '}
                        {product.stock_quantity === null ? 'Unlimited stock' : `${product.stock_quantity} in stock`}
                      </p>
                    </div>
                    <button onClick={() => deleteProductMutation.mutate(product.id)}>
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </button>
                  </div>
                ))}
                {(shopWithProducts?.products || []).length === 0 && (
                  <p className="text-sm text-gray-500">No products yet.</p>
                )}
              </div>
            </div>

            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <h2 className="font-semibold mb-3">Received orders</h2>
              <div className="space-y-2">
                {(receivedOrders || []).map((order) => (
                  <div key={order.id} className="flex items-center justify-between border-t border-gray-100 dark:border-gray-800 pt-2">
                    <div>
                      <p className="text-sm">
                        Qty {order.quantity} · ${(order.total_amount / 100).toFixed(2)}
                      </p>
                      <p className="text-xs text-gray-500 capitalize">{order.status}</p>
                    </div>
                    {order.status === 'pending' && (
                      <div className="flex gap-2">
                        <button
                          onClick={() => fulfillMutation.mutate(order.id)}
                          className="text-xs px-3 py-1 rounded-full bg-green-50 text-green-700 dark:bg-green-900/20"
                        >
                          Fulfill
                        </button>
                        <button
                          onClick={() => cancelMutation.mutate(order.id)}
                          className="text-xs px-3 py-1 rounded-full bg-red-50 text-red-600 dark:bg-red-900/20"
                        >
                          Cancel
                        </button>
                      </div>
                    )}
                  </div>
                ))}
                {(receivedOrders || []).length === 0 && <p className="text-sm text-gray-500">No orders yet.</p>}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
