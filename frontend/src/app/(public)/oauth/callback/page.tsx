'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Loader2, AlertCircle } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import client from '@/lib/api';

function OAuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setUser } = useAuthStore();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get('code');
    const provider = searchParams.get('provider') || sessionStorage.getItem('oauth_provider');
    const state = searchParams.get('state');
    const redirectUri = sessionStorage.getItem('oauth_redirect_uri') || `${window.location.origin}/oauth/callback`;

    if (!code || !provider || !state) {
      setError('Missing OAuth authorization code');
      return;
    }

    client
      .post('/api/auth/oauth/callback', { provider, code, state, redirect_uri: redirectUri })
      .then((res) => {
        localStorage.setItem('token', res.data.access_token);
        setUser(res.data.user);
        router.push('/');
      })
      .catch(() => {
        setError('OAuth sign-in failed. Please try again.');
      });
  }, [searchParams, router, setUser]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center max-w-sm">
          <AlertCircle className="w-10 h-10 text-red-600 mx-auto mb-4" />
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={() => router.push('/login')}
            className="text-pink-600 font-semibold hover:underline"
          >
            Back to login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <Loader2 className="w-8 h-8 animate-spin text-pink-600 mx-auto mb-3" />
        <p className="text-gray-600 dark:text-gray-400">Signing you in...</p>
      </div>
    </div>
  );
}

export default function OAuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
        </div>
      }
    >
      <OAuthCallbackContent />
    </Suspense>
  );
}
