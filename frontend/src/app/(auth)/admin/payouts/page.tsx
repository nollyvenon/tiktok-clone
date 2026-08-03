'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { monetizationApi } from '@/lib/api';
import { useAuthStore } from '@/stores/authStore';
import AdminNav from '@/components/features/AdminNav';
import { Loader2, AlertCircle, Wallet } from 'lucide-react';

type StatusFilter = 'pending' | 'completed' | 'cancelled';

export default function AdminPayoutsPage() {
  const { user } = useAuthStore();
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('pending');
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery(
    ['admin-payouts', statusFilter],
    () => monetizationApi.listPayouts(statusFilter, 50),
    { enabled: user?.role === 'admin' }
  );

  const decideMutation = useMutation(
    ({ payoutId, status }: { payoutId: string; status: 'completed' | 'cancelled' }) =>
      monetizationApi.decidePayout(payoutId, status),
    { onSuccess: () => queryClient.invalidateQueries(['admin-payouts']) }
  );

  if (user && user.role !== 'admin') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">You don&apos;t have access to this page.</p>
      </div>
    );
  }

  const payouts = data?.payouts || [];

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-3xl mx-auto px-4">
        <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
          <Wallet className="w-6 h-6 text-pink-600" />
          Admin Dashboard
        </h1>

        <AdminNav />

        <div className="flex gap-2 mb-6">
          {(['pending', 'completed', 'cancelled'] as StatusFilter[]).map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1 text-sm rounded-full capitalize ${
                statusFilter === s
                  ? 'bg-pink-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        {isLoading && (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
          </div>
        )}

        {!!error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-red-600 dark:text-red-400">Failed to load payouts</p>
          </div>
        )}

        {!isLoading && !error && payouts.length === 0 && (
          <p className="text-gray-500 text-sm text-center py-16">No {statusFilter} payouts.</p>
        )}

        <div className="space-y-4">
          {payouts.map((payout) => (
            <div key={payout.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold">${(payout.amount / 100).toFixed(2)}</span>
                <span className="text-xs text-gray-400">{new Date(payout.requested_at).toLocaleString()}</span>
              </div>

              {payout.status === 'pending' && (
                <div className="flex gap-2">
                  <button
                    onClick={() => decideMutation.mutate({ payoutId: payout.id, status: 'completed' })}
                    disabled={decideMutation.isLoading}
                    className="text-xs px-3 py-1.5 rounded-full font-semibold bg-green-50 text-green-700 hover:bg-green-100 dark:bg-green-900/20 disabled:opacity-50"
                  >
                    Mark Paid
                  </button>
                  <button
                    onClick={() => decideMutation.mutate({ payoutId: payout.id, status: 'cancelled' })}
                    disabled={decideMutation.isLoading}
                    className="text-xs px-3 py-1.5 rounded-full font-semibold bg-red-50 text-red-600 hover:bg-red-100 dark:bg-red-900/20 disabled:opacity-50"
                  >
                    Cancel
                  </button>
                </div>
              )}

              {payout.status !== 'pending' && payout.notes && (
                <p className="text-xs text-gray-500">{payout.notes}</p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
