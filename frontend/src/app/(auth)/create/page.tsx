'use client';

import { Suspense, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Upload, X, Loader2, AlertCircle, Repeat2, Scissors } from 'lucide-react';
import axios from 'axios';
import { uploadApi } from '@/lib/api';

type Stage = 'idle' | 'requesting-url' | 'uploading' | 'finalizing' | 'creating-draft' | 'done';

export default function CreatePage() {
  return (
    <Suspense fallback={null}>
      <CreatePageContent />
    </Suspense>
  );
}

function CreatePageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const originalVideoId = searchParams.get('originalVideoId') || undefined;
  const remixType = searchParams.get('remixType') as 'duet' | 'stitch' | null;
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string>('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isPublic, setIsPublic] = useState(true);
  const [stage, setStage] = useState<Stage>('idle');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const isSubmitting = stage !== 'idle' && stage !== 'done';

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setPreview(URL.createObjectURL(selectedFile));
    }
  };

  const getVideoDuration = (videoFile: File): Promise<number> => {
    return new Promise((resolve) => {
      const video = document.createElement('video');
      video.preload = 'metadata';
      video.onloadedmetadata = () => {
        URL.revokeObjectURL(video.src);
        resolve(Math.round(video.duration));
      };
      video.src = URL.createObjectURL(videoFile);
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !title) return;
    setError(null);

    try {
      // 1. Request a presigned upload URL
      setStage('requesting-url');
      const { upload_id, presigned_url } = await uploadApi.getPresignedUrl(
        file.name,
        file.size,
        file.type
      );

      // 2. Upload the raw file directly to storage
      setStage('uploading');
      await axios.put(presigned_url, file, {
        headers: { 'Content-Type': file.type },
        onUploadProgress: (evt) => {
          if (evt.total) setUploadProgress(Math.round((evt.loaded / evt.total) * 100));
        },
      });

      // 3. Mark the upload complete
      setStage('finalizing');
      const duration = await getVideoDuration(file);
      await uploadApi.completeUpload(upload_id, presigned_url, '', duration);

      // 4. Create a draft tied to this upload, then publish it immediately
      setStage('creating-draft');
      const draft = await uploadApi.createDraft(
        {
          title,
          description,
          is_public: isPublic,
          ...(originalVideoId && remixType ? { original_video_id: originalVideoId, remix_type: remixType } : {}),
        },
        upload_id
      );
      await uploadApi.publishDraft(draft.id);

      setStage('done');
      router.push('/');
    } catch (err) {
      setStage('idle');
      setUploadProgress(0);
      const message = axios.isAxiosError(err)
        ? err.response?.data?.detail || 'Upload failed. Please try again.'
        : 'Upload failed. Please try again.';
      setError(message);
    }
  };

  const stageLabel: Record<Stage, string> = {
    idle: 'Upload',
    'requesting-url': 'Preparing upload...',
    uploading: `Uploading... ${uploadProgress}%`,
    finalizing: 'Processing video...',
    'creating-draft': 'Publishing...',
    done: 'Done',
  };

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-2xl mx-auto px-4">
        <h1 className="text-3xl font-bold mb-2">Upload a video</h1>
        {originalVideoId && remixType && (
          <p className="text-sm text-gray-500 mb-6 flex items-center gap-1.5">
            {remixType === 'duet' ? <Repeat2 className="w-4 h-4" /> : <Scissors className="w-4 h-4" />}
            Uploading a {remixType} response to{' '}
            <a href={`/watch/${originalVideoId}`} className="text-pink-600 hover:underline">
              this video
            </a>
          </p>
        )}

        {error && (
          <div className="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 flex gap-2">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* File Upload */}
          {!file ? (
            <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-12 text-center">
              <label className="cursor-pointer">
                <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <p className="text-lg font-semibold mb-1">Click to upload a video</p>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  or drag and drop
                </p>
                <p className="text-xs text-gray-500">
                  MP4, MOV or WebM. Max 10GB.
                </p>
                <input
                  type="file"
                  accept="video/*"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </label>
            </div>
          ) : (
            <div className="relative bg-black rounded-lg overflow-hidden aspect-video">
              <video src={preview} controls className="w-full h-full" />
              {!isSubmitting && (
                <button
                  type="button"
                  onClick={() => {
                    setFile(null);
                    setPreview('');
                  }}
                  className="absolute top-4 right-4 p-2 bg-black/50 hover:bg-black/70 rounded-full"
                >
                  <X className="w-5 h-5 text-white" />
                </button>
              )}
              {isSubmitting && stage === 'uploading' && (
                <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/20">
                  <div
                    className="h-full bg-pink-600 transition-all"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              )}
            </div>
          )}

          {/* Form Fields */}
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2">Title *</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                maxLength={150}
                placeholder="Give your video a catchy title"
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-pink-600"
                disabled={isSubmitting}
              />
              <p className="text-xs text-gray-500 mt-1">{title.length}/150</p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                maxLength={2200}
                placeholder="Tell viewers about your video"
                rows={4}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-pink-600 resize-none"
                disabled={isSubmitting}
              />
              <p className="text-xs text-gray-500 mt-1">{description.length}/2200</p>
            </div>

            <div>
              <label className="flex items-center gap-3">
                <input
                  type="radio"
                  checked={isPublic}
                  onChange={() => setIsPublic(true)}
                  disabled={isSubmitting}
                />
                <span className="font-medium">Public</span>
              </label>
              <p className="text-sm text-gray-600 dark:text-gray-400 ml-6">
                Everyone can watch
              </p>
            </div>

            <div>
              <label className="flex items-center gap-3">
                <input
                  type="radio"
                  checked={!isPublic}
                  onChange={() => setIsPublic(false)}
                  disabled={isSubmitting}
                />
                <span className="font-medium">Private</span>
              </label>
              <p className="text-sm text-gray-600 dark:text-gray-400 ml-6">
                Only you can watch
              </p>
            </div>
          </div>

          {/* Submit */}
          <div className="flex gap-4">
            <button
              type="button"
              onClick={() => router.back()}
              disabled={isSubmitting}
              className="flex-1 px-6 py-3 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 font-semibold transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!file || !title || isSubmitting}
              className="flex-1 px-6 py-3 bg-pink-600 hover:bg-pink-700 disabled:bg-gray-400 text-white rounded-lg font-semibold transition flex items-center justify-center gap-2"
            >
              {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
              {stageLabel[stage]}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
