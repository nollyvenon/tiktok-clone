'use client';

import { useEffect, useRef, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useRouter } from 'next/navigation';
import { liveApi } from '@/lib/api';
import { useAuthStore } from '@/stores/authStore';
import { Loader2, AlertCircle, Eye, Radio, Send } from 'lucide-react';

interface LiveStreamPageProps {
  params: { streamId: string };
}

export default function LiveStreamPage({ params }: LiveStreamPageProps) {
  const router = useRouter();
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [chatInput, setChatInput] = useState('');
  const hasJoinedRef = useRef(false);

  const { data: stream, isLoading, error } = useQuery(
    ['live-stream', params.streamId],
    () => liveApi.getStream(params.streamId),
    { refetchInterval: 5000 }
  );

  const { data: messages } = useQuery(
    ['live-chat', params.streamId],
    () => liveApi.getChatMessages(params.streamId),
    { refetchInterval: 3000 }
  );

  useEffect(() => {
    if (hasJoinedRef.current) return;
    hasJoinedRef.current = true;
    liveApi.joinStream(params.streamId).catch(() => {});

    return () => {
      liveApi.leaveStream(params.streamId).catch(() => {});
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.streamId]);

  const sendMutation = useMutation(() => liveApi.postChatMessage(params.streamId, chatInput), {
    onSuccess: () => {
      setChatInput('');
      queryClient.invalidateQueries(['live-chat', params.streamId]);
    },
  });

  const endMutation = useMutation(() => liveApi.endStream(params.streamId), {
    onSuccess: () => router.push('/live'),
  });

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
      </div>
    );
  }

  if (error || !stream) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
        <div className="max-w-2xl mx-auto px-4">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-red-600 dark:text-red-400">Stream not found</p>
          </div>
        </div>
      </div>
    );
  }

  const isOwner = user?.id === stream.creator_id;

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-2xl mx-auto px-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold mb-1">{stream.title}</h1>
            <div className="flex items-center gap-3 text-sm text-gray-500">
              {stream.status === 'live' ? (
                <span className="flex items-center gap-1 text-red-600 font-semibold">
                  <Radio className="w-3.5 h-3.5" /> LIVE
                </span>
              ) : (
                <span className="text-gray-400 font-semibold">Ended</span>
              )}
              <span className="flex items-center gap-1">
                <Eye className="w-3.5 h-3.5" /> {stream.viewer_count} watching
              </span>
            </div>
          </div>
          {isOwner && stream.status === 'live' && (
            <button
              onClick={() => endMutation.mutate()}
              disabled={endMutation.isLoading}
              className="text-sm font-semibold px-4 py-1.5 rounded-full bg-red-50 text-red-600 hover:bg-red-100 dark:bg-red-900/20 disabled:opacity-50"
            >
              End stream
            </button>
          )}
        </div>

        <div className="aspect-video bg-gray-900 rounded-lg flex items-center justify-center mb-6">
          <p className="text-gray-400 text-sm text-center px-6">
            No video preview in this build - live chat and viewer presence are fully functional below.
          </p>
        </div>

        <div className="border border-gray-200 dark:border-gray-700 rounded-lg flex flex-col h-96">
          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {(messages || []).length === 0 && (
              <p className="text-sm text-gray-500 text-center mt-8">No messages yet. Say hello!</p>
            )}
            {(messages || []).map((message) => (
              <p key={message.id} className="text-sm">
                <span className="font-semibold">@{message.username}</span>{' '}
                <span className="text-gray-700 dark:text-gray-300">{message.content}</span>
              </p>
            ))}
          </div>
          {stream.status === 'live' && (
            <div className="flex gap-2 p-3 border-t border-gray-100 dark:border-gray-800">
              <input
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && chatInput && sendMutation.mutate()}
                placeholder="Say something..."
                className="flex-1 border border-gray-300 dark:border-gray-700 dark:bg-gray-800 rounded-full px-4 py-2 text-sm"
              />
              <button
                onClick={() => sendMutation.mutate()}
                disabled={!chatInput || sendMutation.isLoading}
                className="p-2 rounded-full bg-pink-600 text-white disabled:opacity-50"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
