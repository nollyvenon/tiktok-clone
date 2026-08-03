'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { monetizationApi } from '@/lib/api';
import { Loader2, AlertCircle, Wallet } from 'lucide-react';

const SOURCE_LABEL: Record<string, string> = {
  creator_fund: 'Creator Fund award',
  shop_order: 'Shop order',
};

const STATUS_STYLE: Record<string, string> = {
  pending: 'bg-yellow-50 text-yellow-700 dark:bg-yellow-900/20',
  completed: 'bg-green-50 text-green-700 dark:bg-green-900/20',
  cancelled: 'bg-gray-100 text-gray-600 dark:bg-gray-800',
};

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5">
      <p className="text-sm text-gray-500 mb-1">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}

export default function MonetizationPage() {
  const queryClient = useQueryClient();
  const [payoutAmount, setPayoutAmount] = useState('');
  const [payoutError, setPayoutError] = useState<string | null>(null);

  const { data: summary, isLoading, error } = useQuery(['monetization-summary'], () => monetizationApi.getSummary());
  const { data: myPayouts } = useQuery(['my-payouts'], () => monetizationApi.getMyPayouts());

  const requestPayoutMutation = useMutation(
    () => monetizationApi.requestPayout(Math.round(Number(payoutAmount) * 100)),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['monetization-summary']);
        queryClient.invalidateQueries(['my-payouts']);
        setPayoutAmount('');
        setPayoutError(null);
      },
      onError: (err: unknown) => {
        const message =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          'Failed to request payout';
        setPayoutError(message);
      },
    }
  );

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
        <div className="max-w-3xl mx-auto px-4">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-red-600 dark:text-red-400">Failed to load your earnings</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-3xl mx-auto px-4">
        <h1 className="text-3xl font-bold mb-8 flex items-center gap-2">
          <Wallet className="w-7 h-7 text-pink-600" />
          Monetization
        </h1>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
          <StatCard label="Total Earned" value={`$${(summary.total_earned / 100).toFixed(2)}`} />
          <StatCard label="Paid Out" value={`$${(summary.total_paid_out / 100).toFixed(2)}`} />
          <StatCard label="Pending Payouts" value={`$${(summary.pending_payout_total / 100).toFixed(2)}`} />
          <StatCard label="Available Balance" value={`$${(summary.available_balance / 100).toFixed(2)}`} />
        </div>

        <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 mb-10">
          <h2 className="font-semibold mb-3">Request a payout</h2>
          <div className="flex gap-2">
            <input
              value={payoutAmount}
              onChange={(e) => setPayoutAmount(e.target.value)}
              type="number"
              placeholder="Amount ($)"
              className="flex-1 border border-gray-300 dark:border-gray-700 dark:bg-gray-800 rounded-lg px-3 py-2 text-sm"
            />
            <button
              onClick={() => requestPayoutMutation.mutate()}
              disabled={!payoutAmount || requestPayoutMutation.isLoading}
              className="bg-pink-600 text-white rounded-full px-4 py-2 text-sm font-semibold disabled:opacity-50"
            >
              Request
            </button>
          </div>
          {payoutError && <p className="text-xs text-red-600 mt-2">{payoutError}</p>}
        </div>

        <h2 className="text-xl font-bold mb-4">Payout requests</h2>
        <div className="space-y-2 mb-10">
          {(myPayouts || []).length === 0 && <p className="text-sm text-gray-500">No payout requests yet.</p>}
          {(myPayouts || []).map((payout) => (
            <div key={payout.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex items-center justify-between">
              <div>
                <p className="text-sm">${(payout.amount / 100).toFixed(2)}</p>
                <p className="text-xs text-gray-400">{new Date(payout.requested_at).toLocaleString()}</p>
                {payout.notes && <p className="text-xs text-gray-500 mt-1">{payout.notes}</p>}
              </div>
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full capitalize ${STATUS_STYLE[payout.status]}`}>
                {payout.status}
              </span>
            </div>
          ))}
        </div>

        <h2 className="text-xl font-bold mb-4">Earnings history</h2>
        <div className="space-y-2">
          {summary.earnings.length === 0 && <p className="text-sm text-gray-500">No earnings yet.</p>}
          {summary.earnings.map((earning) => (
            <div key={earning.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex items-center justify-between">
              <p className="text-sm">{SOURCE_LABEL[earning.source_type]}</p>
              <div className="text-right">
                <p className="text-sm font-semibold">+${(earning.amount / 100).toFixed(2)}</p>
                <p className="text-xs text-gray-400">{new Date(earning.created_at).toLocaleString()}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
