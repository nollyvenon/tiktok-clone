'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Loader2, Heart, UserPlus, MessageCircle, Bell, Trash2, CheckCheck } from 'lucide-react';
import { notificationApi, type NotificationItem } from '@/lib/api';

const TYPE_ICONS: Record<string, React.ElementType> = {
  follow: UserPlus,
  like: Heart,
  comment: MessageCircle,
  mention: MessageCircle,
  message: MessageCircle,
};

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      const data = await notificationApi.getNotifications(50);
      setNotifications(data.notifications);
      setUnreadCount(data.unread_count);
    } catch {
      setError('Failed to load notifications');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleMarkRead = async (id: string) => {
    try {
      await notificationApi.markAsRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch {
      setError('Failed to mark notification as read');
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationApi.markAllAsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch {
      setError('Failed to mark all as read');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await notificationApi.deleteNotification(id);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
    } catch {
      setError('Failed to delete notification');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-2xl mx-auto px-4">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Bell className="w-6 h-6" />
            Notifications
          </h1>
          <div className="flex items-center gap-4">
            <Link href="/settings/notifications" className="text-sm text-pink-600 hover:underline">
              Settings
            </Link>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400 hover:text-pink-600"
              >
                <CheckCheck className="w-4 h-4" />
                Mark all read
              </button>
            )}
          </div>
        </div>

        {error && <p className="text-red-600 text-sm mb-6">{error}</p>}

        {notifications.length === 0 ? (
          <p className="text-gray-500 text-center py-16">No notifications yet</p>
        ) : (
          <div className="divide-y divide-gray-100 dark:divide-gray-800">
            {notifications.map((notification) => {
              const Icon = TYPE_ICONS[notification.type] ?? Bell;
              return (
                <div
                  key={notification.id}
                  className={`flex items-start gap-3 py-4 px-2 -mx-2 rounded ${
                    !notification.is_read ? 'bg-pink-50 dark:bg-pink-900/10' : ''
                  }`}
                >
                  <div className="p-2 rounded-full bg-gray-100 dark:bg-gray-800 flex-shrink-0">
                    <Icon className="w-4 h-4 text-pink-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm">{notification.title}</p>
                    {notification.message && (
                      <p className="text-xs text-gray-500 mt-1">{notification.message}</p>
                    )}
                    <p className="text-xs text-gray-400 mt-1">
                      {new Date(notification.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-1 flex-shrink-0">
                    {!notification.is_read && (
                      <button
                        onClick={() => handleMarkRead(notification.id)}
                        className="p-2 text-gray-400 hover:text-pink-600"
                        title="Mark as read"
                      >
                        <CheckCheck className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(notification.id)}
                      className="p-2 text-gray-400 hover:text-red-600"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
