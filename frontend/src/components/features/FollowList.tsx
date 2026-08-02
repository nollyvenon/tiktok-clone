'use client';

import { useState } from 'react';
import { useQuery } from 'react-query';
import Link from 'next/link';
import { profileApi, FollowListUser } from '@/lib/api';
import { Loader2, AlertCircle, Search } from 'lucide-react';

interface FollowListProps {
  userId: string;
  mode: 'followers' | 'following';
}

export default function FollowList({ userId, mode }: FollowListProps) {
  const [search, setSearch] = useState('');

  const { data, isLoading, error } = useQuery(['follow-list', mode, userId], () =>
    mode === 'followers' ? profileApi.getFollowers(userId, 100, 0) : profileApi.getFollowing(userId, 100, 0)
  );

  const title = mode === 'followers' ? 'Followers' : 'Following';
  const users = (data?.users || []).filter((u) =>
    u.username.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-2xl mx-auto px-4">
        <h1 className="text-2xl font-bold mb-6">{title}</h1>

        <div className="relative mb-6">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={`Search ${title.toLowerCase()}...`}
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
            <p className="text-red-600 dark:text-red-400">Failed to load {title.toLowerCase()}</p>
          </div>
        )}

        {data && users.length === 0 && (
          <p className="text-gray-600 dark:text-gray-400 text-sm">
            {search ? 'No matches found.' : `No ${title.toLowerCase()} yet.`}
          </p>
        )}

        <div className="space-y-1">
          {users.map((user) => (
            <FollowListRow key={user.id} user={user} />
          ))}
        </div>
      </div>
    </div>
  );
}

function FollowListRow({ user }: { user: FollowListUser }) {
  return (
    <Link
      href={`/profile/${user.id}`}
      className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition"
    >
      <img
        src={user.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${user.username}`}
        alt={user.username}
        className="w-11 h-11 rounded-full"
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="font-semibold text-sm truncate">@{user.username}</span>
          {user.is_verified && <span className="text-blue-500 text-xs">✓</span>}
        </div>
        {user.is_followed_by && (
          <span className="text-xs text-gray-500">Follows you</span>
        )}
      </div>
      {user.is_following && (
        <span className="text-xs px-3 py-1 rounded-full bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
          Following
        </span>
      )}
    </Link>
  );
}
