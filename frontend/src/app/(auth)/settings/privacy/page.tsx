'use client';

import { useQuery, useMutation, useQueryClient } from 'react-query';
import Link from 'next/link';
import { profileApi } from '@/lib/api';
import SettingsNav from '@/components/features/SettingsNav';
import { Loader2, AlertCircle } from 'lucide-react';

export default function PrivacySettingsPage() {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery(['blocked-users'], () => profileApi.getBlockedUsers());

  const unblockMutation = useMutation((userId: string) => profileApi.blockUser(userId), {
    onSuccess: () => queryClient.invalidateQueries(['blocked-users']),
  });

  const users = data?.users || [];

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-12 px-4">
      <div className="max-w-md mx-auto">
        <SettingsNav />
        <h1 className="text-3xl font-bold mb-2">Privacy</h1>
        <p className="text-gray-600 dark:text-gray-400 mb-8">Manage who you&apos;ve blocked</p>

        {isLoading && (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
          </div>
        )}

        {!!error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-red-600 dark:text-red-400">Failed to load blocked users</p>
          </div>
        )}

        {!error && !isLoading && users.length === 0 && (
          <p className="text-gray-500 text-sm">You haven&apos;t blocked anyone.</p>
        )}

        <div className="space-y-2">
          {users.map((u) => (
            <div
              key={u.id}
              className="flex items-center gap-3 p-3 border border-gray-200 dark:border-gray-700 rounded-lg"
            >
              <Link href={`/profile/${u.id}`} className="flex items-center gap-3 flex-1 min-w-0">
                <img
                  src={u.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${u.username}`}
                  alt={u.username}
                  className="w-10 h-10 rounded-full"
                />
                <p className="font-semibold text-sm truncate">@{u.username}</p>
              </Link>
              <button
                onClick={() => unblockMutation.mutate(u.id)}
                disabled={unblockMutation.isLoading}
                className="text-xs px-3 py-1.5 rounded-full font-semibold bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-50"
              >
                Unblock
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
