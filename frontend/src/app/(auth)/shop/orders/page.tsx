'use client';

import { useQuery } from 'react-query';
import { shopApi } from '@/lib/api';
import { Loader2, AlertCircle, Receipt } from 'lucide-react';

const STATUS_STYLE: Record<string, string> = {
  pending: 'bg-yellow-50 text-yellow-700 dark:bg-yellow-900/20',
  fulfilled: 'bg-green-50 text-green-700 dark:bg-green-900/20',
  cancelled: 'bg-gray-100 text-gray-600 dark:bg-gray-800',
};

export default function MyOrdersPage() {
  const { data, isLoading, error } = useQuery(['my-orders'], () => shopApi.getMyOrders());

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-2xl mx-auto px-4">
        <h1 className="text-3xl font-bold mb-8 flex items-center gap-2">
          <Receipt className="w-7 h-7 text-pink-600" />
          My Orders
        </h1>

        {isLoading && (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
          </div>
        )}

        {!!error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-red-600 dark:text-red-400">Failed to load your orders</p>
          </div>
        )}

        {!isLoading && !error && (data || []).length === 0 && (
          <p className="text-gray-500 text-sm text-center py-16">You haven&apos;t ordered anything yet.</p>
        )}

        <div className="space-y-3">
          {(data || []).map((order) => (
            <div key={order.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex items-center justify-between">
              <div>
                <p className="text-sm">
                  Qty {order.quantity} · ${(order.total_amount / 100).toFixed(2)}
                </p>
                <p className="text-xs text-gray-400">{new Date(order.created_at).toLocaleString()}</p>
              </div>
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full capitalize ${STATUS_STYLE[order.status]}`}>
                {order.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
