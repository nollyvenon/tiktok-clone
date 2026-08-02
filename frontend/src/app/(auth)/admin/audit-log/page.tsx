'use client';

import { useQuery } from 'react-query';
import { adminApi } from '@/lib/api';
import { useAuthStore } from '@/stores/authStore';
import AdminNav from '@/components/features/AdminNav';
import { Loader2, AlertCircle, ShieldCheck } from 'lucide-react';

export default function AdminAuditLogPage() {
  const { user } = useAuthStore();
  const { data, isLoading, error } = useQuery(['admin-audit-log'], () => adminApi.getAuditLog(50, 0), {
    enabled: user?.role === 'admin',
  });

  if (user && user.role !== 'admin') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">You don&apos;t have access to this page.</p>
      </div>
    );
  }

  const entries = data?.entries || [];

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
            <p className="text-red-600 dark:text-red-400">Failed to load the audit log</p>
          </div>
        )}

        {!error && entries.length === 0 && (
          <p className="text-gray-500 text-sm text-center py-16">No moderation decisions yet.</p>
        )}

        <div className="space-y-3">
          {entries.map((entry) => (
            <div key={entry.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-semibold">
                  {entry.action.replace('_', ' ')} · {entry.report_content_type} report ({entry.report_reason.replace('_', ' ')})
                </span>
                <span className="text-xs text-gray-400">{new Date(entry.created_at).toLocaleString()}</span>
              </div>
              <p className="text-xs text-gray-500">by @{entry.moderator_username}</p>
              {entry.notes && <p className="text-sm text-gray-700 dark:text-gray-300 mt-2">{entry.notes}</p>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
