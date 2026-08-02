'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation } from 'react-query';
import { videoApi, profileApi } from '@/lib/api';
import { Loader2, AlertCircle, Heart, Share2, Bookmark } from 'lucide-react';
import Link from 'next/link';
import CommentSection from '@/components/features/CommentSection';

interface WatchPageProps {
  params: { id: string };
}

export default function WatchPage({ params }: WatchPageProps) {
  const [isLiked, setIsLiked] = useState(false);
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [likeCount, setLikeCount] = useState(0);
  const [isFollowing, setIsFollowing] = useState(false);

  const { data: video, isLoading: videoLoading, error: videoError } = useQuery(
    ['video', params.id],
    () => videoApi.getVideo(params.id)
  );

  useEffect(() => {
    if (video) {
      videoApi.trackView(params.id);
      setIsLiked(video.is_liked);
      setIsBookmarked(video.is_bookmarked);
      setLikeCount(video.likes_count);
    }
  }, [video, params.id]);

  const likeMutation = useMutation(() => videoApi.toggleLike(params.id), {
    onSuccess: (result) => {
      setIsLiked(result.is_liked);
      setLikeCount(result.likes_count);
    },
  });

  const bookmarkMutation = useMutation(() => videoApi.toggleBookmark(params.id), {
    onSuccess: (result) => {
      setIsBookmarked(result.is_bookmarked);
    },
  });

  const followMutation = useMutation(
    () => profileApi.followUser(video!.user.id),
    {
      onSuccess: (result) => setIsFollowing(result.is_following),
    }
  );

  if (videoLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
      </div>
    );
  }

  if (videoError || !video) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-900 pt-8">
        <div className="max-w-4xl mx-auto px-4">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-red-600 dark:text-red-400">Video not found</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Video */}
          <div className="lg:col-span-2">
            <div className="bg-black rounded-lg overflow-hidden aspect-video mb-6">
              <video
                src={video.video_url}
                controls
                className="w-full h-full"
              />
            </div>

            {/* Video Info */}
            <h1 className="text-2xl font-bold mb-2">{video.title}</h1>
            <p className="text-gray-600 dark:text-gray-400 mb-6">{video.description}</p>

            {/* Stats */}
            <div className="flex items-center gap-6 mb-6 pb-6 border-b border-gray-200 dark:border-gray-800">
              <div>
                <p className="text-2xl font-bold">{video.views_count.toLocaleString()}</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Views</p>
              </div>
              <div>
                <p className="text-2xl font-bold">{likeCount}</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Likes</p>
              </div>
              <div>
                <p className="text-2xl font-bold">{video.comments_count}</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Comments</p>
              </div>
            </div>

            {/* Creator */}
            <Link
              href={`/profile/${video.user.id}`}
              className="flex items-center gap-4 mb-6 p-4 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition"
            >
              <img
                src={video.user.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${video.user.username}`}
                alt={video.user.username}
                className="w-12 h-12 rounded-full"
              />
              <div>
                <p className="font-semibold">@{video.user.username}</p>
              </div>
              <button
                onClick={(e) => {
                  e.preventDefault();
                  followMutation.mutate();
                }}
                disabled={followMutation.isLoading}
                className={`ml-auto px-6 py-2 rounded-full font-semibold ${
                  isFollowing
                    ? 'bg-gray-200 dark:bg-gray-700'
                    : 'bg-pink-600 text-white hover:bg-pink-700'
                }`}
              >
                {isFollowing ? 'Following' : 'Follow'}
              </button>
            </Link>

            {/* Actions */}
            <div className="flex items-center gap-4 mb-8">
              <button
                onClick={() => likeMutation.mutate()}
                disabled={likeMutation.isLoading}
                className="flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition disabled:opacity-50"
              >
                <Heart className={`w-5 h-5 ${isLiked ? 'fill-red-600 text-red-600' : ''}`} />
                <span>Like</span>
              </button>
              <button
                onClick={() => bookmarkMutation.mutate()}
                disabled={bookmarkMutation.isLoading}
                className="flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition disabled:opacity-50"
              >
                <Bookmark className={`w-5 h-5 ${isBookmarked ? 'fill-blue-600 text-blue-600' : ''}`} />
                <span>Save</span>
              </button>
              <button className="flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition">
                <Share2 className="w-5 h-5" />
                <span>Share</span>
              </button>
            </div>

            <CommentSection videoId={params.id} videoOwnerId={video.user.id} />
          </div>

          {/* Sidebar - Related Videos */}
          <div>
            <h2 className="text-xl font-bold mb-6">More from this creator</h2>
            <div className="space-y-4">
              <p className="text-gray-600 dark:text-gray-400 text-sm">More videos loading...</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
