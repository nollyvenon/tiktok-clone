'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useMutation } from 'react-query';
import { videoApi } from '@/lib/api';
import type { Video } from '@/types';
import { Heart, MessageCircle, Share2, Bookmark } from 'lucide-react';

interface VideoCardProps {
  video: Video;
  onVideoClick?: () => void;
}

export function VideoCard({ video, onVideoClick }: VideoCardProps) {
  const [isLiked, setIsLiked] = useState(video.is_liked);
  const [isBookmarked, setIsBookmarked] = useState(video.is_bookmarked);
  const [likeCount, setLikeCount] = useState(video.likes_count);

  const likeMutation = useMutation(() => videoApi.toggleLike(video.id), {
    onSuccess: (result) => {
      setIsLiked(result.is_liked);
      setLikeCount(result.likes_count);
    },
  });

  const bookmarkMutation = useMutation(() => videoApi.toggleBookmark(video.id), {
    onSuccess: (result) => {
      setIsBookmarked(result.is_bookmarked);
    },
  });

  const duration = video.duration ?? 0;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg overflow-hidden hover:shadow-lg transition-shadow">
      {/* Thumbnail */}
      <Link href={`/watch/${video.id}`} onClick={onVideoClick}>
        <div className="relative aspect-video bg-gray-900 overflow-hidden group cursor-pointer">
          <img
            src={video.thumbnail_url || 'https://via.placeholder.com/400x300?text=Video'}
            alt={video.title || ''}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
            <div className="w-12 h-12 rounded-full bg-white/30 flex items-center justify-center backdrop-blur-sm">
              <svg
                className="w-6 h-6 text-white fill-current"
                viewBox="0 0 24 24"
              >
                <path d="M8 5v14l11-7z" />
              </svg>
            </div>
          </div>
          <div className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
            {Math.floor(duration / 60)}:{(duration % 60).toString().padStart(2, '0')}
          </div>
        </div>
      </Link>

      {/* Info */}
      <div className="p-4">
        <Link href={`/watch/${video.id}`}>
          <h3 className="font-semibold text-lg line-clamp-2 hover:text-pink-600 transition mb-2">
            {video.title}
          </h3>
        </Link>

        {/* Creator Info */}
        <Link
          href={`/profile/${video.user.id}`}
          className="flex items-center gap-2 mb-3"
        >
          <img
            src={video.user.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${video.user.username}`}
            alt={video.user.username}
            className="w-8 h-8 rounded-full"
          />
          <div className="min-w-0">
            <p className="text-sm font-semibold truncate">
              @{video.user.username}
            </p>
          </div>
        </Link>

        {/* Stats */}
        <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400 mb-3">
          <span>{video.views_count.toLocaleString()} views</span>
          <span>{video.comments_count} comments</span>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => likeMutation.mutate()}
            disabled={likeMutation.isLoading}
            className="flex items-center gap-1 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition disabled:opacity-50"
          >
            <Heart
              className={`w-5 h-5 ${isLiked ? 'fill-red-600 text-red-600' : ''}`}
            />
            <span className="text-sm">{likeCount}</span>
          </button>

          <Link
            href={`/watch/${video.id}`}
            className="flex items-center gap-1 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition"
          >
            <MessageCircle className="w-5 h-5" />
            <span className="text-sm">{video.comments_count}</span>
          </Link>

          <button
            onClick={() => bookmarkMutation.mutate()}
            disabled={bookmarkMutation.isLoading}
            className="flex items-center gap-1 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition disabled:opacity-50"
          >
            <Bookmark
              className={`w-5 h-5 ${isBookmarked ? 'fill-blue-600 text-blue-600' : ''}`}
            />
          </button>

          <button className="flex items-center gap-1 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition ml-auto">
            <Share2 className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
