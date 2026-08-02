'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Loader2, Trash2, Send, Calendar, Pencil } from 'lucide-react';
import { uploadApi } from '@/lib/api';

interface Draft {
  id: string;
  title: string | null;
  description: string | null;
  status: string;
  scheduled_publish_at: string | null;
  created_at: string;
}

export default function DraftsPage() {
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actioningId, setActioningId] = useState<string | null>(null);

  const loadDrafts = async () => {
    setIsLoading(true);
    try {
      const res = await uploadApi.getUserDrafts();
      setDrafts(res.drafts as Draft[]);
    } catch {
      setError('Failed to load drafts');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDrafts();
  }, []);

  const handlePublish = async (draftId: string) => {
    setActioningId(draftId);
    try {
      await uploadApi.publishDraft(draftId);
      setDrafts((prev) => prev.filter((d) => d.id !== draftId));
    } catch {
      setError('Failed to publish draft');
    } finally {
      setActioningId(null);
    }
  };

  const handleDelete = async (draftId: string) => {
    setActioningId(draftId);
    try {
      await uploadApi.deleteDraft(draftId);
      setDrafts((prev) => prev.filter((d) => d.id !== draftId));
    } catch {
      setError('Failed to delete draft');
    } finally {
      setActioningId(null);
    }
  };

  const handleSchedule = async (draftId: string) => {
    const input = window.prompt('Publish at (YYYY-MM-DDTHH:MM), e.g. 2026-08-15T14:30');
    if (!input) return;
    setActioningId(draftId);
    try {
      await uploadApi.scheduleDraft(draftId, input);
      await loadDrafts();
    } catch {
      setError('Failed to schedule draft');
    } finally {
      setActioningId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-2xl mx-auto px-4">
        <h1 className="text-3xl font-bold mb-8">Your drafts</h1>

        {error && (
          <p className="text-red-600 dark:text-red-400 mb-4 text-sm">{error}</p>
        )}

        {drafts.length === 0 ? (
          <p className="text-gray-500">No drafts yet. Upload a video to get started.</p>
        ) : (
          <div className="space-y-4">
            {drafts.map((draft) => (
              <div
                key={draft.id}
                className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex items-start justify-between gap-4"
              >
                <div className="min-w-0">
                  <h3 className="font-semibold truncate">{draft.title || 'Untitled draft'}</h3>
                  {draft.description && (
                    <p className="text-sm text-gray-500 truncate">{draft.description}</p>
                  )}
                  <p className="text-xs text-gray-400 mt-1">
                    Status: {draft.status}
                    {draft.scheduled_publish_at &&
                      ` · Scheduled for ${new Date(draft.scheduled_publish_at).toLocaleString()}`}
                  </p>
                </div>
                <div className="flex gap-2 flex-shrink-0">
                  <Link
                    href={`/edit/${draft.id}`}
                    className="p-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800"
                    title="Edit"
                  >
                    <Pencil className="w-4 h-4" />
                  </Link>
                  <button
                    onClick={() => handleSchedule(draft.id)}
                    disabled={actioningId === draft.id}
                    className="p-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800"
                    title="Schedule"
                  >
                    <Calendar className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handlePublish(draft.id)}
                    disabled={actioningId === draft.id}
                    className="p-2 rounded-lg bg-pink-600 hover:bg-pink-700 text-white"
                    title="Publish now"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(draft.id)}
                    disabled={actioningId === draft.id}
                    className="p-2 rounded-lg border border-red-300 dark:border-red-800 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
