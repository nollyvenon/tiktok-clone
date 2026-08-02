'use client';

import { useEffect, useState } from 'react';
import { Loader2, TrendingUp } from 'lucide-react';
import { hashtagApi, type HashtagAnalytics } from '@/lib/api';

interface HashtagAnalyticsPageProps {
  params: { hashtag: string };
}

export default function HashtagAnalyticsPage({ params }: HashtagAnalyticsPageProps) {
  const hashtag = decodeURIComponent(params.hashtag);
  const [analytics, setAnalytics] = useState<HashtagAnalytics[]>([]);
  const [stats, setStats] = useState<{
    usage_count: number;
    unique_creators: number;
    popularity_score: number;
    trend_velocity: number;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([hashtagApi.getAnalytics(hashtag, 30), hashtagApi.getStats(hashtag)])
      .then(([analyticsData, statsData]) => {
        // Oldest first, for a left-to-right chart
        setAnalytics([...analyticsData].reverse());
        setStats(statsData);
      })
      .catch(() => setError('Failed to load hashtag analytics'))
      .finally(() => setIsLoading(false));
  }, [hashtag]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
      </div>
    );
  }

  if (error) {
    return <div className="min-h-screen flex items-center justify-center text-red-600">{error}</div>;
  }

  const maxUsage = Math.max(...analytics.map((a) => a.usage_count), 1);

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-3xl mx-auto px-4">
        <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
          <TrendingUp className="w-6 h-6 text-pink-600" />
          #{hashtag}
        </h1>

        {stats && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 my-8">
            <div>
              <p className="text-2xl font-bold">{stats.usage_count.toLocaleString()}</p>
              <p className="text-xs text-gray-500">Total posts</p>
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.unique_creators.toLocaleString()}</p>
              <p className="text-xs text-gray-500">Creators</p>
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.popularity_score}</p>
              <p className="text-xs text-gray-500">Popularity</p>
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.trend_velocity.toFixed(0)}%</p>
              <p className="text-xs text-gray-500">Growth</p>
            </div>
          </div>
        )}

        <h2 className="text-lg font-bold mb-4">Usage over the last 30 days</h2>
        {analytics.length === 0 ? (
          <p className="text-gray-500 text-sm">No analytics data yet</p>
        ) : (
          <div className="flex items-end gap-1 h-48 border-b border-gray-200 dark:border-gray-700">
            {analytics.map((day) => (
              <div
                key={day.id}
                className="flex-1 bg-pink-500 hover:bg-pink-600 transition-colors rounded-t min-w-[4px]"
                style={{ height: `${Math.max((day.usage_count / maxUsage) * 100, 2)}%` }}
                title={`${new Date(day.date).toLocaleDateString()}: ${day.usage_count} posts`}
              />
            ))}
          </div>
        )}
        <div className="flex justify-between text-xs text-gray-400 mt-2">
          <span>{analytics[0] && new Date(analytics[0].date).toLocaleDateString()}</span>
          <span>
            {analytics[analytics.length - 1] &&
              new Date(analytics[analytics.length - 1].date).toLocaleDateString()}
          </span>
        </div>
      </div>
    </div>
  );
}
