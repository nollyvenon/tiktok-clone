'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Loader2, ThumbsUp, ThumbsDown, Sparkles } from 'lucide-react';
import { recommendationApi, type Recommendation } from '@/lib/api';

const ALGORITHM_LABELS: Record<string, string> = {
  collaborative: 'Because people like you watched this',
  content_based: 'Similar to videos you liked',
  trending: 'Trending now',
  social: 'From creators you follow',
};

export default function ForYouPage() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedbackGiven, setFeedbackGiven] = useState<Record<string, 'relevant' | 'irrelevant'>>({});

  const load = async () => {
    try {
      const data = await recommendationApi.getForYouFeed(20);
      setRecommendations(data.recommendations);
      setCursor(data.cursor);
    } catch {
      setError('Failed to load your For You feed');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const loadMore = async () => {
    if (!cursor || isLoadingMore) return;
    setIsLoadingMore(true);
    try {
      const data = await recommendationApi.getForYouFeed(20, cursor);
      setRecommendations((prev) => [...prev, ...data.recommendations]);
      setCursor(data.cursor);
    } catch {
      setError('Failed to load more recommendations');
    } finally {
      setIsLoadingMore(false);
    }
  };

  const handleFeedback = async (recommendationId: string, type: 'relevant' | 'irrelevant') => {
    setFeedbackGiven((prev) => ({ ...prev, [recommendationId]: type }));
    try {
      await recommendationApi.recordFeedback(recommendationId, type);
    } catch {
      // Non-critical: feedback failures shouldn't block browsing
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
        <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-pink-600" />
          For You
        </h1>
        <p className="text-gray-500 text-sm mb-8">
          Personalized picks, ranked by our recommendation engine
        </p>

        {error && <p className="text-red-600 text-sm mb-6">{error}</p>}

        {recommendations.length === 0 ? (
          <p className="text-gray-500 text-center py-16">
            No personalized recommendations yet. Watch and like some videos to get started.
          </p>
        ) : (
          <div className="space-y-6">
            {recommendations.map((rec) => {
              const feedback = feedbackGiven[rec.id];
              return (
                <div
                  key={rec.id}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
                >
                  <Link href={`/watch/${rec.video.id}`} className="block">
                    <div className="aspect-video bg-gray-900 relative">
                      {rec.video.thumbnail_url && (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={rec.video.thumbnail_url}
                          alt={rec.video.title || ''}
                          className="w-full h-full object-cover"
                        />
                      )}
                    </div>
                  </Link>
                  <div className="p-4">
                    <p className="text-xs text-gray-500 mb-1">
                      {ALGORITHM_LABELS[rec.algorithm] ?? rec.reason ?? rec.algorithm}
                    </p>
                    <Link href={`/watch/${rec.video.id}`}>
                      <h3 className="font-semibold hover:text-pink-600 transition">
                        {rec.video.title}
                      </h3>
                    </Link>
                    <p className="text-sm text-gray-500">@{rec.video.user.username}</p>

                    <div className="flex items-center gap-2 mt-3">
                      <button
                        onClick={() => handleFeedback(rec.id, 'relevant')}
                        disabled={!!feedback}
                        className={`p-2 rounded-full transition ${
                          feedback === 'relevant'
                            ? 'bg-green-100 text-green-700'
                            : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500'
                        }`}
                        title="More like this"
                      >
                        <ThumbsUp className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleFeedback(rec.id, 'irrelevant')}
                        disabled={!!feedback}
                        className={`p-2 rounded-full transition ${
                          feedback === 'irrelevant'
                            ? 'bg-red-100 text-red-700'
                            : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500'
                        }`}
                        title="Not interested"
                      >
                        <ThumbsDown className="w-4 h-4" />
                      </button>
                      {feedback && (
                        <span className="text-xs text-gray-400">Thanks for the feedback</span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {cursor && (
          <div className="flex justify-center mt-8">
            <button
              onClick={loadMore}
              disabled={isLoadingMore}
              className="px-6 py-3 bg-pink-600 hover:bg-pink-700 disabled:bg-gray-400 text-white font-semibold rounded-lg transition-colors flex items-center gap-2"
            >
              {isLoadingMore && <Loader2 className="w-4 h-4 animate-spin" />}
              {isLoadingMore ? 'Loading more...' : 'Load More'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
