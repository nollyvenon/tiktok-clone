'use client';

import { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import { videoApi } from '@/lib/api';
import { VideoCard } from '@/components/features/VideoCard';
import { Loader2, AlertCircle, Bookmark } from 'lucide-react';

export default function BookmarksPage() {
  const { data, isLoading, error } = useQuery(['bookmarks'], () => videoApi.getBookmarks(50, 0));
  const [removedIds, setRemovedIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    setRemovedIds(new Set());
  }, [data]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
      </div>
    );
  }

  const videos = (data?.videos || []).filter((v) => !removedIds.has(v.id));

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <h1 className="text-3xl font-bold mb-8 flex items-center gap-2">
          <Bookmark className="w-7 h-7 text-pink-600" />
          Saved Videos
        </h1>

        {!!error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-red-600 dark:text-red-400">Failed to load your saved videos</p>
          </div>
        )}

        {!error && videos.length === 0 && (
          <p className="text-gray-600 dark:text-gray-400 text-center py-16">
            You haven&apos;t saved any videos yet. Tap the bookmark icon on a video to save it here.
          </p>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {videos.map((video) => (
            <VideoCard
              key={video.id}
              video={video}
              onBookmarkChange={(isBookmarked) => {
                if (!isBookmarked) {
                  setRemovedIds((prev) => new Set(prev).add(video.id));
                }
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
