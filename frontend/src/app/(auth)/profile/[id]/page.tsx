'use client';

import { useState } from 'react';
import { useQuery, useMutation } from 'react-query';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { profileApi, videoApi, messageApi } from '@/lib/api';
import { VideoCard } from '@/components/features/VideoCard';
import { Loader2, AlertCircle, MessageCircle, SlidersHorizontal, MoreVertical, Ban, Flag } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import ReportModal from '@/components/features/ReportModal';

interface ProfilePageProps {
  params: { id: string };
}

export default function ProfilePage({ params }: ProfilePageProps) {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'videos' | 'likes'>('videos');
  const [showMenu, setShowMenu] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const { user: currentUser } = useAuthStore();

  const { data: profile, isLoading: profileLoading, error: profileError, refetch: refetchProfile } = useQuery(
    ['profile', params.id],
    () => profileApi.getProfile(params.id)
  );

  const { data: videosData, isLoading: videosLoading } = useQuery(
    ['user-videos', params.id],
    () => videoApi.getUserVideos(params.id),
    { enabled: !!profile && activeTab === 'videos' }
  );

  const followMutation = useMutation(() => profileApi.followUser(params.id));

  const messageMutation = useMutation(() => messageApi.startConversation(params.id), {
    onSuccess: (conversation) => {
      router.push(`/messages/${conversation.id}`);
    },
  });

  const blockMutation = useMutation(() => profileApi.blockUser(params.id), {
    onSuccess: () => {
      setShowMenu(false);
      refetchProfile();
    },
  });

  if (profileLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
      </div>
    );
  }

  if (profileError || !profile) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-900 pt-8">
        <div className="max-w-4xl mx-auto px-4">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-red-600 dark:text-red-400">User not found</p>
          </div>
        </div>
      </div>
    );
  }

  const { user, statistics, is_following, is_blocked } = profile;
  const isBlocked = blockMutation.data?.is_blocked ?? is_blocked;
  const isFollowing = followMutation.data?.is_following ?? is_following;
  const followersCount = followMutation.data?.followers_count ?? statistics.followers_count;
  const videos = videosData?.videos || [];
  const isOwnProfile = currentUser?.id === user.id;
  const displayName = user.first_name && user.last_name
    ? `${user.first_name} ${user.last_name}`
    : user.username;

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900">
      {/* Cover */}
      <div
        className="h-48 bg-gradient-to-r from-pink-400 to-purple-500"
        style={user.cover_url ? {
          backgroundImage: `url(${user.cover_url})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        } : undefined}
      />

      {/* Profile Info */}
      <div className="max-w-4xl mx-auto px-4 pb-8">
        <div className="flex flex-col sm:flex-row sm:items-end gap-4 -mt-20 mb-8">
          <img
            src={user.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${user.username}`}
            alt={user.username}
            className="w-32 h-32 rounded-full border-4 border-white dark:border-gray-900"
          />

          <div className="flex-1">
            <h1 className="text-3xl font-bold mb-1">
              {displayName}
              {user.is_verified && <span className="ml-2 text-blue-500">✓</span>}
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mb-2">@{user.username}</p>
            {user.bio && (
              <p className="text-gray-700 dark:text-gray-300 mb-4">{user.bio}</p>
            )}
          </div>

          {!isOwnProfile && (
            <div className="flex gap-2 relative">
              <button
                onClick={() => followMutation.mutate()}
                disabled={followMutation.isLoading || isBlocked}
                className={`px-6 py-2 rounded-full font-semibold transition disabled:opacity-50 ${
                  isFollowing
                    ? 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600'
                    : 'bg-pink-600 text-white hover:bg-pink-700'
                }`}
              >
                {isFollowing ? 'Following' : 'Follow'}
              </button>
              <button
                onClick={() => messageMutation.mutate()}
                disabled={messageMutation.isLoading || isBlocked}
                className="p-2 rounded-full border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50"
              >
                <MessageCircle className="w-5 h-5" />
              </button>
              <button
                onClick={() => setShowMenu((v) => !v)}
                className="p-2 rounded-full border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800"
              >
                <MoreVertical className="w-5 h-5" />
              </button>
              {showMenu && (
                <div className="absolute right-0 top-full mt-2 w-48 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-10">
                  <button
                    onClick={() => {
                      setShowMenu(false);
                      setShowReportModal(true);
                    }}
                    className="w-full flex items-center gap-2 px-4 py-3 text-left hover:bg-gray-100 dark:hover:bg-gray-700 rounded-t-lg"
                  >
                    <Flag className="w-4 h-4" />
                    Report @{user.username}
                  </button>
                  <button
                    onClick={() => blockMutation.mutate()}
                    disabled={blockMutation.isLoading}
                    className="w-full flex items-center gap-2 px-4 py-3 text-left text-red-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-b-lg disabled:opacity-50"
                  >
                    <Ban className="w-4 h-4" />
                    {isBlocked ? 'Unblock' : 'Block'} @{user.username}
                  </button>
                </div>
              )}
            </div>
          )}
          {isBlocked && !isOwnProfile && (
            <p className="text-sm text-red-600 mt-2">You have blocked this user.</p>
          )}
          {showReportModal && (
            <ReportModal contentType="user" contentId={user.id} onClose={() => setShowReportModal(false)} />
          )}

          {isOwnProfile && (
            <Link
              href="/settings/preferences"
              className="p-2 rounded-full border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800"
              title="For You Preferences"
            >
              <SlidersHorizontal className="w-5 h-5" />
            </Link>
          )}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-8 mb-8 pb-8 border-b border-gray-200 dark:border-gray-800">
          <div>
            <p className="text-2xl font-bold">{statistics.videos_count}</p>
            <p className="text-gray-600 dark:text-gray-400">Videos</p>
          </div>
          <Link href={`/profile/${params.id}/followers`} className="hover:opacity-70 transition">
            <p className="text-2xl font-bold">{followersCount.toLocaleString()}</p>
            <p className="text-gray-600 dark:text-gray-400">Followers</p>
          </Link>
          <Link href={`/profile/${params.id}/following`} className="hover:opacity-70 transition">
            <p className="text-2xl font-bold">{statistics.following_count}</p>
            <p className="text-gray-600 dark:text-gray-400">Following</p>
          </Link>
        </div>

        {/* Tabs */}
        <div className="flex gap-8 mb-8 border-b border-gray-200 dark:border-gray-800">
          <button
            onClick={() => setActiveTab('videos')}
            className={`pb-4 font-semibold border-b-2 transition ${
              activeTab === 'videos'
                ? 'border-pink-600 text-pink-600'
                : 'border-transparent text-gray-600 dark:text-gray-400'
            }`}
          >
            Videos
          </button>
          <button
            onClick={() => setActiveTab('likes')}
            className={`pb-4 font-semibold border-b-2 transition ${
              activeTab === 'likes'
                ? 'border-pink-600 text-pink-600'
                : 'border-transparent text-gray-600 dark:text-gray-400'
            }`}
          >
            Likes
          </button>
        </div>

        {/* Videos Grid */}
        {activeTab === 'likes' ? (
          <div className="text-center py-16">
            <p className="text-gray-600 dark:text-gray-400">Liked videos are coming soon</p>
          </div>
        ) : videosLoading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
          </div>
        ) : videos.length === 0 ? (
          <div className="text-center py-16">
            <p className="text-gray-600 dark:text-gray-400">No videos yet</p>
          </div>
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
