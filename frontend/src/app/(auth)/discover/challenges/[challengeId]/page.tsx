'use client';

import { useEffect, useState } from 'react';
import { Loader2, Trophy, Users } from 'lucide-react';
import { hashtagApi, type Challenge } from '@/lib/api';
import { VideoCard } from '@/components/features/VideoCard';
import type { Video } from '@/types';

interface ChallengePageProps {
  params: { challengeId: string };
}

export default function ChallengeDetailPage({ params }: ChallengePageProps) {
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [videos, setVideos] = useState<Video[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      hashtagApi.getChallengeDetails(params.challengeId),
      hashtagApi.getChallengeVideos(params.challengeId),
    ])
      .then(([challengeData, videosData]) => {
        setChallenge(challengeData);
        setVideos(videosData.videos);
        setTotal(videosData.total);
      })
      .catch(() => setError('Failed to load challenge'))
      .finally(() => setIsLoading(false));
  }, [params.challengeId]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
      </div>
    );
  }

  if (error || !challenge) {
    return (
      <div className="min-h-screen flex items-center justify-center text-red-600">
        {error || 'Challenge not found'}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-5xl mx-auto px-4">
        <div className="mb-8">
          <div className="flex items-center gap-2 text-amber-500 mb-2">
            <Trophy className="w-5 h-5" />
            <span className="text-sm font-semibold">Challenge</span>
          </div>
          <h1 className="text-3xl font-bold mb-2">#{challenge.hashtag}</h1>
          <p className="text-xl text-gray-700 dark:text-gray-300 mb-4">{challenge.title}</p>
          {challenge.description && (
            <p className="text-gray-600 dark:text-gray-400 mb-4">{challenge.description}</p>
          )}
          <div className="flex items-center gap-6 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <Users className="w-4 h-4" />
              {challenge.participation_count.toLocaleString()} entries
            </span>
            {challenge.prize_pool != null && (
              <span className="font-semibold text-amber-600">
                ${challenge.prize_pool.toLocaleString()} prize pool
              </span>
            )}
            <span className={challenge.is_active ? 'text-green-600' : 'text-gray-400'}>
              {challenge.is_active ? 'Active' : 'Ended'}
            </span>
          </div>
        </div>

        <h2 className="text-xl font-bold mb-4">Entries ({total})</h2>
        {videos.length === 0 ? (
          <p className="text-gray-500 text-center py-16">No entries yet — be the first!</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {videos.map((video) => (
              <VideoCard key={video.id} video={video} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
