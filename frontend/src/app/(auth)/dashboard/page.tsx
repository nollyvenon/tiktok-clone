'use client';

import { useQuery } from 'react-query';
import Link from 'next/link';
import { videoApi } from '@/lib/api';
import { Loader2, AlertCircle, Eye, Heart, MessageCircle, Users, BarChart3, DollarSign, Handshake, Store } from 'lucide-react';

function StatCard({ label, value, icon: Icon }: { label: string; value: string | number; icon: typeof Eye }) {
  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5">
      <div className="flex items-center gap-2 text-gray-500 mb-2">
        <Icon className="w-4 h-4" />
        <span className="text-sm">{label}</span>
      </div>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}

export default function DashboardPage() {
  const { data, isLoading, error } = useQuery(['creator-dashboard'], () => videoApi.getDashboard(10));

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-red-600 dark:text-red-400">Failed to load your dashboard</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <BarChart3 className="w-7 h-7 text-pink-600" />
            Creator Dashboard
          </h1>
          <div className="flex items-center gap-4">
            <Link
              href="/creator-fund"
              className="flex items-center gap-1.5 text-sm font-semibold text-pink-600 hover:text-pink-700"
            >
              <DollarSign className="w-4 h-4" />
              Creator Fund
            </Link>
            <Link
              href="/collaborations"
              className="flex items-center gap-1.5 text-sm font-semibold text-pink-600 hover:text-pink-700"
            >
              <Handshake className="w-4 h-4" />
              Collaborations
            </Link>
            <Link
              href="/shop/manage"
              className="flex items-center gap-1.5 text-sm font-semibold text-pink-600 hover:text-pink-700"
            >
              <Store className="w-4 h-4" />
              My Shop
            </Link>
          </div>
        </div>
        <p className="text-gray-500 text-sm mb-8">
          Aggregate performance across all {data.video_count} of your videos
        </p>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
          <StatCard label="Total Views" value={data.total_views.toLocaleString()} icon={Eye} />
          <StatCard label="Total Likes" value={data.total_likes.toLocaleString()} icon={Heart} />
          <StatCard label="Total Comments" value={data.total_comments.toLocaleString()} icon={MessageCircle} />
          <StatCard label="Followers" value={data.followers_count.toLocaleString()} icon={Users} />
        </div>

        <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4 mb-10 flex items-center justify-between">
          <span className="text-sm text-gray-600 dark:text-gray-400">Average engagement rate</span>
          <span className="text-lg font-bold">{data.average_engagement_rate}%</span>
        </div>

        <h2 className="text-xl font-bold mb-4">Top Videos</h2>
        {data.top_videos.length === 0 ? (
          <p className="text-gray-500 text-sm">
            No videos yet. Once you publish, your top performers will show up here.
          </p>
        ) : (
          <div className="space-y-2">
            {data.top_videos.map((video, index) => (
              <Link
                key={video.video_id}
                href={`/watch/${video.video_id}`}
                className="flex items-center gap-4 p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition"
              >
                <span className="w-6 text-center text-gray-400 font-semibold">{index + 1}</span>
                <img
                  src={video.thumbnail_url || 'https://via.placeholder.com/80x60?text=Video'}
                  alt={video.title || ''}
                  className="w-20 h-14 object-cover rounded"
                />
                <div className="flex-1 min-w-0">
                  <p className="font-semibold truncate">{video.title || 'Untitled'}</p>
                  <p className="text-sm text-gray-500">
                    {video.views.toLocaleString()} views · {video.likes.toLocaleString()} likes ·{' '}
                    {video.comments.toLocaleString()} comments
                  </p>
                </div>
                <span className="text-sm font-semibold text-pink-600 flex-shrink-0">
                  {video.engagement_rate}%
                </span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
