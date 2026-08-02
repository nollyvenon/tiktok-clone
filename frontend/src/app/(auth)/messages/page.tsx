'use client';

import { useQuery } from 'react-query';
import Link from 'next/link';
import { messageApi } from '@/lib/api';
import { Loader2, AlertCircle, MessageCircle } from 'lucide-react';

function timeAgo(iso: string): string {
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h`;
  return `${Math.floor(hours / 24)}d`;
}

export default function MessagesPage() {
  const { data, isLoading, error } = useQuery(['conversations'], () =>
    messageApi.getConversations(50, 0)
  );

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
      </div>
    );
  }

  const conversations = data?.conversations || [];

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-2xl mx-auto px-4">
        <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
          <MessageCircle className="w-6 h-6" />
          Messages
        </h1>

        {!!error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-red-600 dark:text-red-400">Failed to load conversations</p>
          </div>
        )}

        {!error && conversations.length === 0 && (
          <p className="text-gray-600 dark:text-gray-400 text-sm text-center py-16">
            No conversations yet. Visit a profile and tap the message icon to start one.
          </p>
        )}

        <div className="space-y-1">
          {conversations.map((c) => (
            <Link
              key={c.id}
              href={`/messages/${c.id}`}
              className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition"
            >
              <img
                src={
                  c.other_user.avatar_url ||
                  `https://api.dicebear.com/7.x/avataaars/svg?seed=${c.other_user.username}`
                }
                alt={c.other_user.username}
                className="w-12 h-12 rounded-full flex-shrink-0"
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-sm truncate">
                    @{c.other_user.username}
                  </span>
                  <span className="text-xs text-gray-500 flex-shrink-0 ml-2">
                    {timeAgo(c.updated_at)}
                  </span>
                </div>
                <p
                  className={`text-sm truncate ${
                    c.unread_count > 0
                      ? 'font-semibold text-gray-900 dark:text-gray-100'
                      : 'text-gray-500'
                  }`}
                >
                  {c.last_message?.content || 'No messages yet'}
                </p>
              </div>
              {c.unread_count > 0 && (
                <span className="w-2.5 h-2.5 rounded-full bg-pink-600 flex-shrink-0" />
              )}
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
