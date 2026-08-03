'use client';

import { useEffect, useState } from 'react';
import { Loader2, CheckCircle2 } from 'lucide-react';
import { notificationApi, type NotificationPreferences } from '@/lib/api';
import SettingsNav from '@/components/features/SettingsNav';

const TYPE_TOGGLES: Array<{ key: keyof NotificationPreferences; label: string }> = [
  { key: 'follow_notifications', label: 'New followers' },
  { key: 'like_notifications', label: 'Likes' },
  { key: 'comment_notifications', label: 'Comments' },
  { key: 'mention_notifications', label: 'Mentions' },
  { key: 'message_notifications', label: 'Direct messages' },
];

const CHANNEL_TOGGLES: Array<{ key: keyof NotificationPreferences; label: string }> = [
  { key: 'push_enabled', label: 'Push notifications' },
  { key: 'email_enabled', label: 'Email notifications' },
  { key: 'in_app_enabled', label: 'In-app notifications' },
];

export default function NotificationSettingsPage() {
  const [prefs, setPrefs] = useState<NotificationPreferences | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    notificationApi
      .getPreferences()
      .then(setPrefs)
      .catch(() => setError('Failed to load notification settings'))
      .finally(() => setIsLoading(false));
  }, []);

  const handleToggle = async (key: keyof NotificationPreferences, value: boolean) => {
    if (!prefs) return;
    setPrefs({ ...prefs, [key]: value });
    setSaved(false);
    try {
      const updated = await notificationApi.updatePreferences({ [key]: value });
      setPrefs(updated);
      setSaved(true);
    } catch {
      setError('Failed to save');
    }
  };

  const handleDigestChange = async (frequency: string) => {
    if (!prefs) return;
    setPrefs({ ...prefs, email_digest_frequency: frequency });
    setSaved(false);
    try {
      const updated = await notificationApi.updatePreferences({ email_digest_frequency: frequency });
      setPrefs(updated);
      setSaved(true);
    } catch {
      setError('Failed to save');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
      </div>
    );
  }

  if (error && !prefs) {
    return <div className="min-h-screen flex items-center justify-center text-red-600">{error}</div>;
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-12 px-4">
      <div className="max-w-md mx-auto">
        <SettingsNav />
        <h1 className="text-3xl font-bold mb-2">Notification settings</h1>
        <p className="text-gray-600 dark:text-gray-400 mb-8">Choose what you get notified about</p>

        {saved && (
          <div className="flex items-center gap-2 text-green-600 text-sm mb-4">
            <CheckCircle2 className="w-4 h-4" /> Saved
          </div>
        )}
        {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

        {prefs && (
          <div className="space-y-8">
            <div>
              <h2 className="text-sm font-semibold text-gray-500 mb-3">Channels</h2>
              <div className="space-y-3">
                {CHANNEL_TOGGLES.map(({ key, label }) => (
                  <label key={key} className="flex items-center justify-between">
                    <span>{label}</span>
                    <input
                      type="checkbox"
                      checked={Boolean(prefs[key])}
                      onChange={(e) => handleToggle(key, e.target.checked)}
                      className="w-5 h-5 accent-pink-600"
                    />
                  </label>
                ))}
              </div>
            </div>

            <div>
              <h2 className="text-sm font-semibold text-gray-500 mb-3">Notify me about</h2>
              <div className="space-y-3">
                {TYPE_TOGGLES.map(({ key, label }) => (
                  <label key={key} className="flex items-center justify-between">
                    <span>{label}</span>
                    <input
                      type="checkbox"
                      checked={Boolean(prefs[key])}
                      onChange={(e) => handleToggle(key, e.target.checked)}
                      className="w-5 h-5 accent-pink-600"
                    />
                  </label>
                ))}
              </div>
            </div>

            <div>
              <h2 className="text-sm font-semibold text-gray-500 mb-3">Email digest</h2>
              <select
                value={prefs.email_digest_frequency}
                onChange={(e) => handleDigestChange(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="never">Never</option>
              </select>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
