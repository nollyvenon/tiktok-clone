'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { moderationApi, type ReportStatus, type ModerationActionType } from '@/lib/api';
import { useAuthStore } from '@/stores/authStore';
import { Loader2, AlertCircle, ShieldAlert } from 'lucide-react';

const ACTIONS: { value: ModerationActionType; label: string; danger?: boolean }[] = [
  { value: 'dismiss', label: 'Dismiss' },
  { value: 'remove_content', label: 'Remove content', danger: true },
  { value: 'warn_user', label: 'Warn user' },
  { value: 'suspend_user', label: 'Suspend user', danger: true },
  { value: 'ban_user', label: 'Ban user', danger: true },
];

export default function ModerationQueuePage() {
  const { user } = useAuthStore();
  const [statusFilter, setStatusFilter] = useState<ReportStatus>('pending');
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery(
    ['moderation-queue', statusFilter],
    () => moderationApi.getReportQueue({ status: statusFilter, limit: 50 }),
    { enabled: user?.role === 'admin' }
  );

  const decideMutation = useMutation(
    ({ reportId, action }: { reportId: string; action: ModerationActionType }) =>
      moderationApi.decideReport(reportId, action),
    { onSuccess: () => queryClient.invalidateQueries(['moderation-queue']) }
  );

  if (user && user.role !== 'admin') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">You don&apos;t have access to this page.</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
      </div>
    );
  }

  const reports = data?.reports || [];

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-3xl mx-auto px-4">
        <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
          <ShieldAlert className="w-6 h-6 text-pink-600" />
          Moderation Queue
        </h1>

        <div className="flex gap-2 mb-6">
          {(['pending', 'actioned', 'dismissed'] as ReportStatus[]).map((s) => (
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

        {!!error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-red-600 dark:text-red-400">Failed to load the report queue</p>
          </div>
        )}

        {!error && reports.length === 0 && (
          <p className="text-gray-500 text-sm text-center py-16">No {statusFilter} reports.</p>
        )}

        <div className="space-y-4">
          {reports.map((report) => (
            <div
              key={report.id}
              className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold uppercase text-gray-500">
                  {report.content_type} · {report.reason.replace('_', ' ')}
                </span>
                <span className="text-xs text-gray-400">
                  {new Date(report.created_at).toLocaleString()}
                </span>
              </div>
              {report.description && (
                <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">{report.description}</p>
              )}
              <p className="text-xs text-gray-500 mb-3">
                Target ID: {report.reported_video_id || report.reported_comment_id || report.reported_user_id}
              </p>

              {report.status === 'pending' && (
                <div className="flex flex-wrap gap-2">
                  {ACTIONS.map((action) => (
                    <button
                      key={action.value}
                      onClick={() => decideMutation.mutate({ reportId: report.id, action: action.value })}
                      disabled={decideMutation.isLoading}
                      className={`text-xs px-3 py-1.5 rounded-full font-semibold disabled:opacity-50 ${
                        action.danger
                          ? 'bg-red-50 text-red-600 hover:bg-red-100 dark:bg-red-900/20'
                          : 'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700'
                      }`}
                    >
                      {action.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
