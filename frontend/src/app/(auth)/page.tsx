'use client';

import { useState } from 'react';
import { useInfiniteQuery } from 'react-query';
import { videoApi } from '@/lib/api';
import type { FeedResponse } from '@/types';
import { VideoCard } from '@/components/features/VideoCard';
import { AlertCircle, Loader2 } from 'lucide-react';

export default function HomePage() {
  const [feedType, setFeedType] = useState<'foryou' | 'following'>('foryou');

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetching,
    isLoading,
    error,
  } = useInfiniteQuery(
    ['videos', 'feed', feedType],
    async ({ pageParam = 0 }) => {
      return videoApi.getFeed(feedType === 'following' ? 'following' : 'for_you', pageParam);
    },
    {
      // Offset-based pagination: the backend's `cursor` field is always
      // null, so the next page's offset is derived from how many videos
      // we've loaded so far.
      getNextPageParam: (lastPage, allPages) => {
        const loaded = allPages.flatMap((p) => p.videos).length;
        if (lastPage.total != null && loaded >= lastPage.total) return undefined;
        if (lastPage.videos.length === 0) return undefined;
        return loaded;
      },
    }
  );

  const videos = data?.pages.flatMap((page) => page.videos) || [];

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900">
      {/* Tabs */}
      <div className="sticky top-16 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 z-40">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex gap-8">
            <button
              onClick={() => setFeedType('foryou')}
              className={`py-4 font-semibold border-b-2 transition ${
                feedType === 'foryou'
                  ? 'border-pink-600 text-pink-600'
                  : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              For You
            </button>
            <button
              onClick={() => setFeedType('following')}
              className={`py-4 font-semibold border-b-2 transition ${
                feedType === 'following'
                  ? 'border-pink-600 text-pink-600'
                  : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              Following
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {!!error && (
          <div className="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-red-600 dark:text-red-400 mb-1">
                Error loading videos
              </h3>
              <p className="text-sm text-red-500 dark:text-red-300">
                Failed to load videos. Please try again.
              </p>
            </div>
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <div className="text-center">
              <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2 text-pink-600" />
              <p className="text-gray-600 dark:text-gray-400">Loading videos...</p>
            </div>
          </div>
        ) : videos.length === 0 ? (
          <div className="flex items-center justify-center py-16">
            <div className="text-center">
              <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-semibold mb-1">No videos yet</h3>
              <p className="text-gray-600 dark:text-gray-400">
                {feedType === 'following'
                  ? 'Follow creators to see their videos'
                  : 'Check back later for new videos'}
              </p>
            </div>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {videos.map((video) => (
                <VideoCard key={video.id} video={video} />
              ))}
            </div>

            {hasNextPage && (
              <div className="flex justify-center mt-8">
                <button
                  onClick={() => fetchNextPage()}
                  disabled={isFetching}
                  className="px-6 py-3 bg-pink-600 hover:bg-pink-700 disabled:bg-gray-400 text-white font-semibold rounded-lg transition-colors flex items-center gap-2"
                >
                  {isFetching && <Loader2 className="w-4 h-4 animate-spin" />}
                  {isFetching ? 'Loading more...' : 'Load More'}
                </button>
              </div>
            )}

            {isFetching && hasNextPage === false && (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                No more videos to load
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
