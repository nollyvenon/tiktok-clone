'use client';

import { useState } from 'react';
import { useQuery, useMutation } from 'react-query';
import { useRouter } from 'next/navigation';
import { liveApi } from '@/lib/api';
import { Loader2, AlertCircle, Radio, Eye } from 'lucide-react';

export default function LiveDiscoveryPage() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [startError, setStartError] = useState<string | null>(null);

  const { data: streams, isLoading, error } = useQuery(['live-streams'], () => liveApi.listLiveStreams(), {
    refetchInterval: 10000,
  });

  const startMutation = useMutation(() => liveApi.startStream(title), {
    onSuccess: (stream) => router.push(`/live/${stream.id}`),
    onError: (err: unknown) => {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Failed to start stream';
      setStartError(message);
    },
  });

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-3xl mx-auto px-4">
        <h1 className="text-3xl font-bold mb-8 flex items-center gap-2">
          <Radio className="w-7 h-7 text-pink-600" />
          Live
        </h1>

        <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 mb-10">
          <h2 className="font-semibold mb-3">Go live</h2>
          <div className="flex gap-2">
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Stream title"
              className="flex-1 border border-gray-300 dark:border-gray-700 dark:bg-gray-800 rounded-lg px-3 py-2 text-sm"
            />
            <button
              onClick={() => startMutation.mutate()}
              disabled={!title || startMutation.isLoading}
              className="bg-pink-600 text-white rounded-full px-4 py-2 text-sm font-semibold disabled:opacity-50"
            >
              Start
            </button>
          </div>
          {startError && <p className="text-xs text-red-600 mt-2">{startError}</p>}
        </div>

        <h2 className="text-xl font-bold mb-4">Live now</h2>

        {isLoading && (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
          </div>
        )}

        {!!error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-red-600 dark:text-red-400">Failed to load live streams</p>
          </div>
        )}

        {!isLoading && !error && (streams || []).length === 0 && (
          <p className="text-gray-500 text-sm text-center py-16">No one is live right now.</p>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {(streams || []).map((stream) => (
            <button
              key={stream.id}
              onClick={() => router.push(`/live/${stream.id}`)}
              className="text-left border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:border-pink-400 transition"
            >
              <div className="flex items-center gap-1.5 mb-2">
                <span className="w-2 h-2 rounded-full bg-red-600" />
                <span className="text-xs font-semibold text-red-600">LIVE</span>
              </div>
              <p className="font-semibold mb-1">{stream.title}</p>
              <p className="text-xs text-gray-500 flex items-center gap-1">
                <Eye className="w-3 h-3" />
                {stream.viewer_count} watching
              </p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
