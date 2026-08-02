'use client';

import { useEffect, useState } from 'react';
import { Loader2, CheckCircle2 } from 'lucide-react';
import { recommendationApi, type UserPreferences } from '@/lib/api';

export default function PreferencesPage() {
  const [prefs, setPrefs] = useState<UserPreferences | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [diversity, setDiversity] = useState(0.5);
  const [recency, setRecency] = useState(0.5);
  const [hashtagsInput, setHashtagsInput] = useState('');

  useEffect(() => {
    recommendationApi
      .getPreferences()
      .then((data) => {
        setPrefs(data);
        setDiversity(data.content_diversity_score);
        setRecency(data.recency_preference);
        setHashtagsInput(data.preferred_hashtags.join(', '));
      })
      .catch(() => setError('Failed to load preferences'))
      .finally(() => setIsLoading(false));
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    setSaved(false);
    setError(null);
    try {
      const updated = await recommendationApi.updatePreferences({
        content_diversity_score: diversity,
        recency_preference: recency,
        preferred_hashtags: hashtagsInput
          .split(',')
          .map((h) => h.trim())
          .filter(Boolean),
      });
      setPrefs(updated);
      setSaved(true);
    } catch {
      setError('Failed to save preferences');
    } finally {
      setIsSaving(false);
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
    <div className="min-h-screen bg-white dark:bg-gray-900 py-12 px-4">
      <div className="max-w-md mx-auto">
        <h1 className="text-3xl font-bold mb-2">For You Preferences</h1>
        <p className="text-gray-600 dark:text-gray-400 mb-8">
          Tune how your For You feed is personalized
        </p>

        {error && <p className="text-red-600 text-sm mb-4">{error}</p>}
        {saved && (
          <div className="flex items-center gap-2 text-green-600 text-sm mb-4">
            <CheckCircle2 className="w-4 h-4" /> Preferences saved
          </div>
        )}

        <div className="space-y-8">
          <div>
            <label className="flex justify-between text-sm font-medium mb-2">
              <span>Content diversity</span>
              <span className="text-gray-500">{Math.round(diversity * 100)}%</span>
            </label>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={diversity}
              onChange={(e) => setDiversity(Number(e.target.value))}
              className="w-full"
            />
            <p className="text-xs text-gray-500 mt-1">
              Higher values show a wider mix of creators and topics
            </p>
          </div>

          <div>
            <label className="flex justify-between text-sm font-medium mb-2">
              <span>Prefer recent content</span>
              <span className="text-gray-500">{Math.round(recency * 100)}%</span>
            </label>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={recency}
              onChange={(e) => setRecency(Number(e.target.value))}
              className="w-full"
            />
            <p className="text-xs text-gray-500 mt-1">
              Higher values prioritize newer videos over older popular ones
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Preferred hashtags</label>
            <input
              type="text"
              value={hashtagsInput}
              onChange={(e) => setHashtagsInput(e.target.value)}
              placeholder="dance, comedy, cooking"
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-pink-600"
            />
            <p className="text-xs text-gray-500 mt-1">Comma-separated</p>
          </div>

          <button
            onClick={handleSave}
            disabled={isSaving}
            className="w-full bg-pink-600 hover:bg-pink-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            {isSaving && <Loader2 className="w-4 h-4 animate-spin" />}
            {isSaving ? 'Saving...' : 'Save preferences'}
          </button>
        </div>

        {prefs?.avg_watch_time != null && (
          <p className="text-xs text-gray-400 mt-8 text-center">
            Average watch time: {prefs.avg_watch_time}s
          </p>
        )}
      </div>
    </div>
  );
}
