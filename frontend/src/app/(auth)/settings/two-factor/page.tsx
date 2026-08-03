'use client';

import { useState } from 'react';
import { AlertCircle, CheckCircle2, Loader2, Copy, RefreshCw } from 'lucide-react';
import { authApi } from '@/lib/api';
import SettingsNav from '@/components/features/SettingsNav';

export default function TwoFactorPage() {
  const [qrCode, setQrCode] = useState<string | null>(null);
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [is2FAEnabled, setIs2FAEnabled] = useState(false);

  const handleSetup2FA = async () => {
    setError('');
    setIsLoading(true);
    try {
      const result = await authApi.setup2FA();
      setQrCode(result.qr_code_uri);
    } catch (err) {
      setError('Failed to setup 2FA. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerify2FA = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!code || code.length !== 6) {
      setError('Please enter a valid 6-digit code');
      return;
    }

    setIsVerifying(true);
    try {
      await authApi.verify2FA(code);
      setSuccess('2FA enabled successfully!');
      setQrCode(null);
      setCode('');
      setIs2FAEnabled(true);
    } catch (err) {
      setError('Invalid code. Please try again.');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleDisable2FA = async () => {
    if (!confirm('Are you sure you want to disable 2FA?')) return;

    setError('');
    setIsLoading(true);
    try {
      await authApi.disable2FA();
      setSuccess('2FA disabled successfully');
      setIs2FAEnabled(false);
    } catch (err) {
      setError('Failed to disable 2FA. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-12 px-4">
      <div className="max-w-md mx-auto">
        <SettingsNav />
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Two-Factor Authentication
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mb-8">
          Add an extra layer of security to your account
        </p>

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6 flex gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          </div>
        )}

        {success && (
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 mb-6 flex gap-3">
            <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-green-600 dark:text-green-400">{success}</p>
          </div>
        )}

        {is2FAEnabled && !qrCode ? (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6 mb-6">
            <CheckCircle2 className="w-8 h-8 text-green-600 mb-4" />
            <p className="text-sm text-gray-700 dark:text-gray-300 mb-4">
              Two-factor authentication is enabled on your account.
            </p>
            <button
              onClick={handleDisable2FA}
              disabled={isLoading}
              className="w-full bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded-lg transition-colors"
            >
              {isLoading ? 'Disabling...' : 'Disable 2FA'}
            </button>
          </div>
        ) : null}

        {!qrCode && !is2FAEnabled && (
          <button
            onClick={handleSetup2FA}
            disabled={isLoading}
            className="w-full bg-pink-600 hover:bg-pink-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2 mb-6"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Setting up...
              </>
            ) : (
              'Enable 2FA'
            )}
          </button>
        )}

        {qrCode && (
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Scan QR Code
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Add this account to Google Authenticator, Authy, or a similar app.
              Most apps let you paste this setup key directly if you can&apos;t scan a QR code.
            </p>

            <div className="bg-white dark:bg-gray-900 p-4 rounded-lg mb-6 border border-gray-200 dark:border-gray-700">
              <p className="text-xs text-gray-500 mb-1">Setup key</p>
              <p className="text-sm font-mono break-all select-all">
                {new URLSearchParams(qrCode.split('?')[1]).get('secret') || qrCode}
              </p>
            </div>

            <form onSubmit={handleVerify2FA}>
              <label htmlFor="code" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Enter 6-Digit Code
              </label>
              <input
                id="code"
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="000000"
                maxLength={6}
                className="w-full px-4 py-2 bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white placeholder-gray-500 text-center text-2xl tracking-widest font-mono focus:outline-none focus:ring-2 focus:ring-pink-500 mb-4"
              />

              <button
                type="submit"
                disabled={isVerifying || code.length !== 6}
                className="w-full bg-pink-600 hover:bg-pink-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                {isVerifying ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Verifying...
                  </>
                ) : (
                  'Verify & Enable'
                )}
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
