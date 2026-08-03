'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { collaborationsApi, videoApi, searchApi } from '@/lib/api';
import { useAuthStore } from '@/stores/authStore';
import { Loader2, AlertCircle, Users, X } from 'lucide-react';

interface DraftCollaborator {
  userId: string;
  username: string;
  percent: string;
}

export default function CollaborationsPage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();

  const [videoId, setVideoId] = useState('');
  const [title, setTitle] = useState('');
  const [ownPercent, setOwnPercent] = useState('');
  const [drafts, setDrafts] = useState<DraftCollaborator[]>([]);
  const [inviteQuery, setInviteQuery] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const { data: myVideos } = useQuery(['my-videos-for-collab'], () =>
    videoApi.getUserVideos(user?.id || '', 50, 0)
  , { enabled: !!user });

  const { data: myCollaborations, isLoading, error } = useQuery(
    ['my-collaborations'],
    () => collaborationsApi.listMine()
  );

  const { data: searchResults } = useQuery(
    ['collab-user-search', inviteQuery],
    () => searchApi.searchCreators(inviteQuery, 5),
    { enabled: inviteQuery.length >= 2 }
  );

  const createMutation = useMutation(collaborationsApi.create, {
    onSuccess: () => {
      queryClient.invalidateQueries(['my-collaborations']);
      setVideoId('');
      setTitle('');
      setOwnPercent('');
      setDrafts([]);
      setFormError(null);
    },
    onError: (err: unknown) => {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Failed to create collaboration';
      setFormError(message);
    },
  });

  const respondMutation = useMutation(
    ({ id, accept }: { id: string; accept: boolean }) => collaborationsApi.respond(id, accept),
    { onSuccess: () => queryClient.invalidateQueries(['my-collaborations']) }
  );

  const cancelMutation = useMutation((id: string) => collaborationsApi.cancel(id), {
    onSuccess: () => queryClient.invalidateQueries(['my-collaborations']),
  });

  const addDraftCollaborator = (userId: string, username: string) => {
    if (drafts.some((d) => d.userId === userId)) return;
    setDrafts((prev) => [...prev, { userId, username, percent: '' }]);
    setInviteQuery('');
  };

  const removeDraftCollaborator = (userId: string) => {
    setDrafts((prev) => prev.filter((d) => d.userId !== userId));
  };

  const handleSubmit = () => {
    setFormError(null);
    if (!user) return;
    if (!videoId) {
      setFormError('Choose a video first');
      return;
    }
    const collaborators = [
      { user_id: user.id, revenue_split_percent: Number(ownPercent) },
      ...drafts.map((d) => ({ user_id: d.userId, revenue_split_percent: Number(d.percent) })),
    ];
    createMutation.mutate({ video_id: videoId, title: title || undefined, collaborators });
  };

  const videos = myVideos?.videos || [];
  const collaborations = myCollaborations || [];

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-3xl mx-auto px-4">
        <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
          <Users className="w-7 h-7 text-pink-600" />
          Collaborations
        </h1>
        <p className="text-gray-500 text-sm mb-8">
          Invite other creators to collaborate on a video, with an agreed revenue split.
        </p>

        <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 mb-10">
          <h2 className="font-semibold mb-3">Start a collaboration</h2>

          <label className="block text-sm text-gray-500 mb-1">Video</label>
          <select
            value={videoId}
            onChange={(e) => setVideoId(e.target.value)}
            className="w-full border border-gray-300 dark:border-gray-700 dark:bg-gray-800 rounded-lg px-3 py-2 mb-3 text-sm"
          >
            <option value="">Select one of your videos</option>
            {videos.map((v) => (
              <option key={v.id} value={v.id}>
                {v.title || v.id}
              </option>
            ))}
          </select>

          <label className="block text-sm text-gray-500 mb-1">Title (optional)</label>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full border border-gray-300 dark:border-gray-700 dark:bg-gray-800 rounded-lg px-3 py-2 mb-3 text-sm"
            placeholder="Duet special"
          />

          <label className="block text-sm text-gray-500 mb-1">Your revenue share (%)</label>
          <input
            type="number"
            value={ownPercent}
            onChange={(e) => setOwnPercent(e.target.value)}
            className="w-full border border-gray-300 dark:border-gray-700 dark:bg-gray-800 rounded-lg px-3 py-2 mb-3 text-sm"
            placeholder="60"
          />

          <label className="block text-sm text-gray-500 mb-1">Invite collaborators</label>
          <input
            value={inviteQuery}
            onChange={(e) => setInviteQuery(e.target.value)}
            className="w-full border border-gray-300 dark:border-gray-700 dark:bg-gray-800 rounded-lg px-3 py-2 mb-2 text-sm"
            placeholder="Search by username"
          />
          {inviteQuery.length >= 2 && (searchResults?.results || []).length > 0 && (
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg mb-3 overflow-hidden">
              {(searchResults?.results || []).map((result) => (
                <button
                  key={result.id}
                  onClick={() => addDraftCollaborator(result.id, result.username)}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-800"
                >
                  @{result.username}
                </button>
              ))}
            </div>
          )}

          {drafts.map((draft) => (
            <div key={draft.userId} className="flex items-center gap-2 mb-2">
              <span className="text-sm flex-1">@{draft.username}</span>
              <input
                type="number"
                value={draft.percent}
                onChange={(e) =>
                  setDrafts((prev) =>
                    prev.map((d) => (d.userId === draft.userId ? { ...d, percent: e.target.value } : d))
                  )
                }
                placeholder="%"
                className="w-20 border border-gray-300 dark:border-gray-700 dark:bg-gray-800 rounded-lg px-2 py-1 text-sm"
              />
              <button onClick={() => removeDraftCollaborator(draft.userId)}>
                <X className="w-4 h-4 text-gray-400" />
              </button>
            </div>
          ))}

          {formError && <p className="text-sm text-red-600 mt-2">{formError}</p>}

          <button
            onClick={handleSubmit}
            disabled={createMutation.isLoading}
            className="mt-3 w-full bg-pink-600 text-white rounded-lg py-2 text-sm font-semibold hover:bg-pink-700 disabled:opacity-50"
          >
            {createMutation.isLoading ? 'Creating...' : 'Create collaboration'}
          </button>
        </div>

        <h2 className="text-xl font-bold mb-4">Your Collaborations</h2>

        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
          </div>
        )}

        {!!error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-red-600 dark:text-red-400">Failed to load your collaborations</p>
          </div>
        )}

        {!isLoading && !error && collaborations.length === 0 && (
          <p className="text-gray-500 text-sm">You have no collaborations yet.</p>
        )}

        <div className="space-y-4">
          {collaborations.map((collab) => {
            const mine = collab.collaborators.find((c) => c.user_id === user?.id);
            const isInitiator = collab.initiator_id === user?.id;
            return (
              <div key={collab.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold">{collab.title || 'Untitled collaboration'}</span>
                  <span
                    className={`text-xs font-semibold px-2 py-0.5 rounded-full capitalize ${
                      collab.status === 'active'
                        ? 'bg-green-50 text-green-700 dark:bg-green-900/20'
                        : collab.status === 'cancelled'
                        ? 'bg-gray-100 text-gray-600 dark:bg-gray-800'
                        : 'bg-yellow-50 text-yellow-700 dark:bg-yellow-900/20'
                    }`}
                  >
                    {collab.status}
                  </span>
                </div>
                <ul className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  {collab.collaborators.map((c) => (
                    <li key={c.id}>
                      {c.user_id === user?.id ? 'You' : c.user_id} — {c.revenue_split_percent}% ({c.status})
                    </li>
                  ))}
                </ul>

                {collab.status === 'pending' && mine?.status === 'invited' && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => respondMutation.mutate({ id: collab.id, accept: true })}
                      disabled={respondMutation.isLoading}
                      className="text-xs px-3 py-1.5 rounded-full font-semibold bg-green-50 text-green-700 hover:bg-green-100 dark:bg-green-900/20 disabled:opacity-50"
                    >
                      Accept
                    </button>
                    <button
                      onClick={() => respondMutation.mutate({ id: collab.id, accept: false })}
                      disabled={respondMutation.isLoading}
                      className="text-xs px-3 py-1.5 rounded-full font-semibold bg-red-50 text-red-600 hover:bg-red-100 dark:bg-red-900/20 disabled:opacity-50"
                    >
                      Decline
                    </button>
                  </div>
                )}

                {collab.status === 'pending' && isInitiator && (
                  <button
                    onClick={() => cancelMutation.mutate(collab.id)}
                    disabled={cancelMutation.isLoading}
                    className="text-xs px-3 py-1.5 rounded-full font-semibold bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-50"
                  >
                    Cancel
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
