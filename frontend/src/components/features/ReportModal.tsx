'use client';

import { useState } from 'react';
import { useMutation } from 'react-query';
import { moderationApi, type ReportedContentType, type ReportReason } from '@/lib/api';
import { X } from 'lucide-react';

const REASONS: { value: ReportReason; label: string }[] = [
  { value: 'spam', label: 'Spam' },
  { value: 'harassment', label: 'Harassment or bullying' },
  { value: 'nudity', label: 'Nudity or sexual content' },
  { value: 'violence', label: 'Violence' },
  { value: 'hate_speech', label: 'Hate speech' },
  { value: 'misinformation', label: 'Misinformation' },
  { value: 'self_harm', label: 'Self-harm' },
  { value: 'other', label: 'Other' },
];

interface ReportModalProps {
  contentType: ReportedContentType;
  contentId: string;
  onClose: () => void;
}

export default function ReportModal({ contentType, contentId, onClose }: ReportModalProps) {
  const [reason, setReason] = useState<ReportReason>('spam');
  const [description, setDescription] = useState('');

  const mutation = useMutation(
    () => moderationApi.createReport({ content_type: contentType, content_id: contentId, reason, description: description || undefined }),
    { onSuccess: onClose }
  );

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-white dark:bg-gray-800 rounded-lg max-w-sm w-full p-5"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-bold text-lg">Report {contentType}</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full">
            <X className="w-5 h-5" />
          </button>
        </div>

        {mutation.isSuccess ? (
          <p className="text-sm text-gray-600 dark:text-gray-400 py-4">
            Thanks - your report has been submitted for review.
          </p>
        ) : (
          <>
            <div className="space-y-1 mb-4">
              {REASONS.map((r) => (
                <label key={r.value} className="flex items-center gap-2 text-sm py-1 cursor-pointer">
                  <input
                    type="radio"
                    name="reason"
                    checked={reason === r.value}
                    onChange={() => setReason(r.value)}
                  />
                  {r.label}
                </label>
              ))}
            </div>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Additional details (optional)"
              rows={3}
              maxLength={1000}
              className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-900 mb-4 resize-none"
            />
            {mutation.isError && (
              <p className="text-xs text-red-600 mb-2">Failed to submit report. Please try again.</p>
            )}
            <button
              onClick={() => mutation.mutate()}
              disabled={mutation.isLoading}
              className="w-full py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white font-semibold text-sm disabled:opacity-50"
            >
              {mutation.isLoading ? 'Submitting...' : 'Submit report'}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
