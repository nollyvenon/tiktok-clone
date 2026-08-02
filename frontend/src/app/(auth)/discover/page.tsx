'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Loader2, TrendingUp, Trophy, Flame } from 'lucide-react';
import { hashtagApi, type HashtagTrend, type Challenge } from '@/lib/api';

export default function DiscoverPage() {
  const [trends, setTrends] = useState<HashtagTrend[]>([]);
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([hashtagApi.getTrending('US', 20), hashtagApi.getActiveChallenges('US', 10)])
      .then(([trendsData, challengesData]) => {
        setTrends(trendsData);
        setChallenges(challengesData);
      })
      .catch(() => setError('Failed to load trending content'))
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-3xl mx-auto px-4">
        <h1 className="text-3xl font-bold mb-8">Discover</h1>
        {error && <p className="text-red-600 text-sm mb-6">{error}</p>}

        <section className="mb-12">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Trophy className="w-5 h-5 text-amber-500" />
            Active Challenges
          </h2>
          {challenges.length === 0 ? (
            <p className="text-gray-500 text-sm">No active challenges right now</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {challenges.map((challenge) => (
                <Link
                  key={challenge.id}
                  href={`/discover/challenges/${challenge.id}`}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:border-pink-400 transition-colors block"
                >
                  <p className="font-semibold">#{challenge.hashtag}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{challenge.title}</p>
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>{challenge.participation_count} entries</span>
                    {challenge.prize_pool != null && (
                      <span className="font-semibold text-amber-600">
                        ${challenge.prize_pool.toLocaleString()} prize
                      </span>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>

        <section>
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-pink-600" />
            Trending Hashtags
          </h2>
          {trends.length === 0 ? (
            <p className="text-gray-500 text-sm">No trending hashtags yet</p>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-800">
              {trends.map((trend, index) => (
                <div
                  key={trend.id}
                  className="flex items-center justify-between py-3 px-2 -mx-2 rounded hover:bg-gray-50 dark:hover:bg-gray-800"
                >
                  <Link
                    href={`/discover/hashtags/${encodeURIComponent(trend.hashtag)}`}
                    className="flex items-center gap-3 flex-1 min-w-0"
                  >
                    <span className="text-gray-400 font-mono text-sm w-5">{index + 1}</span>
                    <div className="min-w-0">
                      <p className="font-semibold">#{trend.hashtag}</p>
                      <p className="text-xs text-gray-500">
                        {trend.usage_count.toLocaleString()} posts ·{' '}
                        {trend.unique_creators.toLocaleString()} creators
                      </p>
                    </div>
                  </Link>
                  <div className="flex items-center gap-3 flex-shrink-0">
                    {trend.trend_velocity > 0 && (
                      <span className="flex items-center gap-1 text-xs text-orange-500 font-semibold">
                        <Flame className="w-3 h-3" />
                        {trend.trend_velocity.toFixed(0)}%
                      </span>
                    )}
                    <Link
                      href={`/search?q=${encodeURIComponent(trend.hashtag)}`}
                      className="text-xs text-pink-600 hover:underline"
                    >
                      Videos
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
