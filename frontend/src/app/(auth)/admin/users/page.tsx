'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { adminApi } from '@/lib/api';
import { useAuthStore } from '@/stores/authStore';
import AdminNav from '@/components/features/AdminNav';
import { Loader2, AlertCircle, Search, ShieldCheck } from 'lucide-react';

export default function AdminUsersPage() {
  const { user } = useAuthStore();
  const [search, setSearch] = useState('');
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery(
    ['admin-users', search],
    () => adminApi.getUsers(search || undefined, 50, 0),
    { enabled: user?.role === 'admin' }
  );

  const suspendMutation = useMutation((userId: string) => adminApi.suspendUser(userId), {
    onSuccess: () => queryClient.invalidateQueries(['admin-users']),
  });
  const reactivateMutation = useMutation((userId: string) => adminApi.reactivateUser(userId), {
    onSuccess: () => queryClient.invalidateQueries(['admin-users']),
  });

  if (user && user.role !== 'admin') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">You don&apos;t have access to this page.</p>
      </div>
    );
  }

  const users = data?.users || [];

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
          <ShieldCheck className="w-6 h-6 text-pink-600" />
          Admin Dashboard
        </h1>

        <AdminNav />

        <div className="relative mb-6">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by username or email..."
            className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 dark:bg-gray-800 text-sm"
          />
        </div>

        {isLoading && (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
          </div>
        )}

        {!!error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-red-600 dark:text-red-400">Failed to load users</p>
          </div>
        )}

        <div className="space-y-2">
          {users.map((u) => (
            <div
              key={u.id}
              className="flex items-center gap-3 p-3 border border-gray-200 dark:border-gray-700 rounded-lg"
            >
              <img
                src={u.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${u.username}`}
                alt={u.username}
                className="w-10 h-10 rounded-full"
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="font-semibold text-sm truncate">@{u.username}</p>
                  {u.role === 'admin' && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-pink-100 text-pink-600">admin</span>
                  )}
                  {!u.is_active && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-600">suspended</span>
                  )}
                </div>
                <p className="text-xs text-gray-500 truncate">{u.email}</p>
              </div>
              {u.is_active ? (
                <button
                  onClick={() => suspendMutation.mutate(u.id)}
                  disabled={suspendMutation.isLoading}
                  className="text-xs px-3 py-1.5 rounded-full font-semibold bg-red-50 text-red-600 hover:bg-red-100 dark:bg-red-900/20 disabled:opacity-50"
                >
                  Suspend
                </button>
              ) : (
                <button
                  onClick={() => reactivateMutation.mutate(u.id)}
                  disabled={reactivateMutation.isLoading}
                  className="text-xs px-3 py-1.5 rounded-full font-semibold bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-50"
                >
                  Reactivate
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
