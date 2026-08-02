'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';
import { Navbar } from '@/components/common/Navbar';

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { isAuthenticated, fetchCurrentUser, isLoading } = useAuthStore();

  useEffect(() => {
    // Check if user is authenticated on mount
    if (!isAuthenticated && typeof window !== 'undefined') {
      const token = localStorage.getItem('token');
      if (token) {
        fetchCurrentUser();
      } else {
        router.push('/login');
      }
    }
  }, [isAuthenticated, fetchCurrentUser, router]);

  if (!isAuthenticated && isLoading) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-900 flex items-center justify-center">
        <div className="animate-spin">
          <div className="w-12 h-12 border-4 border-pink-200 dark:border-pink-800 border-t-pink-600 rounded-full" />
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="flex flex-col min-h-screen bg-white dark:bg-gray-900">
      <Navbar />
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
