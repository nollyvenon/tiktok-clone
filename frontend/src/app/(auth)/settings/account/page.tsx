'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { authApi } from '@/lib/api';
import { useAuthStore } from '@/stores/authStore';
import SettingsNav from '@/components/features/SettingsNav';
import { CheckCircle2, Download, AlertTriangle } from 'lucide-react';

export default function AccountSettingsPage() {
  const router = useRouter();
  const { logout } = useAuthStore();

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordSaved, setPasswordSaved] = useState(false);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  const [isExporting, setIsExporting] = useState(false);

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deletePassword, setDeletePassword] = useState('');
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError(null);
    setPasswordSaved(false);
    setIsChangingPassword(true);
    try {
      await authApi.changePassword(currentPassword, newPassword, confirmPassword);
      setPasswordSaved(true);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch {
      setPasswordError('Failed to change password. Check your current password and try again.');
    } finally {
      setIsChangingPassword(false);
    }
  };

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const data = await authApi.exportMyData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'my-data-export.json';
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setIsExporting(false);
    }
  };

  const handleDelete = async () => {
    setDeleteError(null);
    setIsDeleting(true);
    try {
      await authApi.deleteAccount(deletePassword);
      await logout();
      router.push('/login');
    } catch {
      setDeleteError('Failed to delete account. Check your password and try again.');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-12 px-4">
      <div className="max-w-md mx-auto">
        <SettingsNav />
        <h1 className="text-3xl font-bold mb-2">Account</h1>
        <p className="text-gray-600 dark:text-gray-400 mb-8">
          Manage your password, data, and account
        </p>

        <form onSubmit={handleChangePassword} className="space-y-4 mb-12">
          <h2 className="font-semibold">Change password</h2>
          <input
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            placeholder="Current password"
            required
            className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 dark:bg-gray-800 text-sm"
          />
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="New password"
            required
            className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 dark:bg-gray-800 text-sm"
          />
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Confirm new password"
            required
            className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 dark:bg-gray-800 text-sm"
          />
          {passwordError && <p className="text-sm text-red-600">{passwordError}</p>}
          {passwordSaved && (
            <p className="text-sm text-green-600 flex items-center gap-1">
              <CheckCircle2 className="w-4 h-4" /> Password changed
            </p>
          )}
          <button
            type="submit"
            disabled={isChangingPassword}
            className="px-4 py-2 rounded-lg bg-pink-600 hover:bg-pink-700 text-white font-semibold text-sm disabled:opacity-50"
          >
            {isChangingPassword ? 'Saving...' : 'Change password'}
          </button>
        </form>

        <div className="mb-12">
          <h2 className="font-semibold mb-3">Export your data</h2>
          <p className="text-sm text-gray-500 mb-3">
            Download a copy of your profile, videos, and comments.
          </p>
          <button
            onClick={handleExport}
            disabled={isExporting}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800 text-sm font-semibold disabled:opacity-50"
          >
            <Download className="w-4 h-4" />
            {isExporting ? 'Preparing...' : 'Download my data'}
          </button>
        </div>

        <div className="border border-red-200 dark:border-red-900 rounded-lg p-4">
          <h2 className="font-semibold text-red-600 flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4" />
            Delete account
          </h2>
          <p className="text-sm text-gray-500 mb-3">
            This deactivates your account and signs you out everywhere. This cannot be undone from the app.
          </p>
          {!showDeleteConfirm ? (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white font-semibold text-sm"
            >
              Delete my account
            </button>
          ) : (
            <div className="space-y-3">
              <input
                type="password"
                value={deletePassword}
                onChange={(e) => setDeletePassword(e.target.value)}
                placeholder="Enter your password to confirm"
                className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 dark:bg-gray-800 text-sm"
              />
              {deleteError && <p className="text-sm text-red-600">{deleteError}</p>}
              <div className="flex gap-2">
                <button
                  onClick={handleDelete}
                  disabled={isDeleting || !deletePassword}
                  className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white font-semibold text-sm disabled:opacity-50"
                >
                  {isDeleting ? 'Deleting...' : 'Confirm deletion'}
                </button>
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
