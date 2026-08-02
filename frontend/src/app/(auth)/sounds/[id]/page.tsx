'use client';

import { useQuery } from 'react-query';
import { aiApi } from '@/lib/api';
import { VideoCard } from '@/components/features/VideoCard';
import { Loader2, AlertCircle, Music } from 'lucide-react';

interface SoundPageProps {
  params: { id: string };
}

export default function SoundPage({ params }: SoundPageProps) {
  const { data, isLoading, error } = useQuery(['sound-videos', params.id], () =>
    aiApi.getVideosUsingSound(params.id, 50, 0)
  );

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
      </div>
    );
  }

  const videos = data?.videos || [];
  const music = videos[0]?.music;

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <h1 className="text-2xl font-bold mb-2 flex items-center gap-2">
          <Music className="w-6 h-6 text-pink-600" />
          {music?.sound_title || 'Sound'}
        </h1>
        {music?.artist && <p className="text-gray-500 mb-6">{music.artist}</p>}
        <p className="text-sm text-gray-500 mb-8">
          {data?.total ?? 0} {data?.total === 1 ? 'video' : 'videos'} using this sound
        </p>

        {!!error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-red-600 dark:text-red-400">Failed to load videos for this sound</p>
          </div>
        )}

        {!error && videos.length === 0 && (
          <p className="text-gray-600 dark:text-gray-400 text-center py-16">
            No videos have used this sound yet.
          </p>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {videos.map((video) => (
            <VideoCard key={video.id} video={video} />
          ))}
        </div>
      </div>
    </div>
  );
}
