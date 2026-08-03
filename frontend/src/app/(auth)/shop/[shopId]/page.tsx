'use client';

import { useState } from 'react';
import { useQuery, useMutation } from 'react-query';
import { shopApi } from '@/lib/api';
import { Loader2, AlertCircle, Store, ShoppingBag } from 'lucide-react';

interface ShopPageProps {
  params: { shopId: string };
}

export default function ShopPage({ params }: ShopPageProps) {
  const [orderedIds, setOrderedIds] = useState<Set<string>>(new Set());
  const [orderError, setOrderError] = useState<string | null>(null);

  const { data, isLoading, error } = useQuery(['shop', params.shopId], () => shopApi.getShop(params.shopId));

  const orderMutation = useMutation((productId: string) => shopApi.orderProduct(productId, 1), {
    onSuccess: (_data, productId) => {
      setOrderedIds((prev) => new Set(prev).add(productId));
      setOrderError(null);
    },
    onError: (err: unknown) => {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Failed to place order';
      setOrderError(message);
    },
  });

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
        <div className="max-w-3xl mx-auto px-4">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-red-600 dark:text-red-400">Shop not found</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-3xl mx-auto px-4">
        <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
          <Store className="w-7 h-7 text-pink-600" />
          {data.shop.name}
        </h1>
        {data.shop.description && <p className="text-gray-500 text-sm mb-8">{data.shop.description}</p>}

        {orderError && <p className="text-sm text-red-600 mb-4">{orderError}</p>}

        {data.products.length === 0 ? (
          <p className="text-gray-500 text-sm">No products available yet.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {data.products.map((product) => {
              const isOrdered = orderedIds.has(product.id);
              const outOfStock = product.stock_quantity === 0;
              return (
                <div key={product.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                  <p className="font-semibold">{product.name}</p>
                  {product.description && (
                    <p className="text-sm text-gray-500 mt-1">{product.description}</p>
                  )}
                  <p className="text-lg font-bold mt-2">${(product.price / 100).toFixed(2)}</p>
                  <p className="text-xs text-gray-500 mb-3">
                    {product.stock_quantity === null
                      ? 'In stock'
                      : outOfStock
                      ? 'Out of stock'
                      : `${product.stock_quantity} left`}
                  </p>
                  <button
                    onClick={() => orderMutation.mutate(product.id)}
                    disabled={isOrdered || outOfStock || orderMutation.isLoading}
                    className="flex items-center justify-center gap-1.5 w-full bg-pink-600 text-white rounded-full py-1.5 text-sm font-semibold disabled:opacity-50"
                  >
                    <ShoppingBag className="w-4 h-4" />
                    {isOrdered ? 'Ordered' : 'Order'}
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
