'use client';

import { useQuery } from 'react-query';
import { adminApi } from '@/lib/api';
import { useAuthStore } from '@/stores/authStore';
import AdminNav from '@/components/features/AdminNav';
import { Loader2, AlertCircle, ShieldCheck } from 'lucide-react';

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5">
      <p className="text-sm text-gray-500 mb-1">{label}</p>
      <p className="text-2xl font-bold">{value.toLocaleString()}</p>
    </div>
  );
}

export default function AdminOverviewPage() {
  const { user } = useAuthStore();
  const { data, isLoading, error } = useQuery(['admin-stats'], () => adminApi.getStats(), {
    enabled: user?.role === 'admin',
  });

  if (user && user.role !== 'admin') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">You don&apos;t have access to this page.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
          <ShieldCheck className="w-6 h-6 text-pink-600" />
          Admin Dashboard
        </h1>

        <AdminNav />

        {isLoading && (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
          </div>
        )}

        {!!error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-red-600 dark:text-red-400">Failed to load platform stats</p>
          </div>
        )}

        {data && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Total Users" value={data.total_users} />
            <StatCard label="Active Users" value={data.active_users} />
            <StatCard label="Suspended Users" value={data.suspended_users} />
            <StatCard label="Total Videos" value={data.total_videos} />
            <StatCard label="Total Comments" value={data.total_comments} />
            <StatCard label="Pending Reports" value={data.pending_reports} />
            <StatCard label="Actioned Reports" value={data.actioned_reports} />
            <StatCard label="Dismissed Reports" value={data.dismissed_reports} />
          </div>
        )}
      </div>
    </div>
  );
}
