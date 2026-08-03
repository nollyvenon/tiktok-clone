'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';
import { useTheme } from '@/providers/ThemeProvider';
import { notificationApi } from '@/lib/api';
import {
  Menu,
  X,
  Home,
  Search,
  Plus,
  Heart,
  MessageCircle,
  User,
  LogOut,
  Moon,
  Sun,
  Compass,
  Sparkles,
  Bell,
  Bookmark,
  BarChart3,
  Settings,
  Receipt,
} from 'lucide-react';

export function Navbar() {
  const router = useRouter();
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    notificationApi
      .getNotifications(1, 0, true)
      .then((data) => setUnreadCount(data.unread_count))
      .catch(() => {
        // Non-critical: badge just stays at 0 if this fails
      });
  }, []);
  const { user, logout } = useAuthStore();
  const { theme, setTheme, isDark } = useTheme();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
  };

  return (
    <nav className="sticky top-0 z-50 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <span className="text-2xl font-bold text-pink-600">♪</span>
            <span className="font-bold text-xl hidden sm:inline">TikTok</span>
          </Link>

          {/* Desktop Menu */}
          <div className="hidden md:flex items-center gap-8">
            <Link href="/" className="flex items-center gap-2 hover:text-pink-600 transition">
              <Home className="w-5 h-5" />
              <span>Home</span>
            </Link>
            <Link href="/for-you" className="flex items-center gap-2 hover:text-pink-600 transition">
              <Sparkles className="w-5 h-5" />
              <span>For You</span>
            </Link>
            <Link href="/search" className="flex items-center gap-2 hover:text-pink-600 transition">
              <Search className="w-5 h-5" />
              <span>Search</span>
            </Link>
            <Link href="/discover" className="flex items-center gap-2 hover:text-pink-600 transition">
              <Compass className="w-5 h-5" />
              <span>Discover</span>
            </Link>
            <Link href="/create" className="flex items-center gap-2 hover:text-pink-600 transition">
              <Plus className="w-5 h-5" />
              <span>Create</span>
            </Link>
          </div>

          {/* Right Actions */}
          <div className="flex items-center gap-4">
            {/* Messages */}
            <Link
              href="/messages"
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition"
              title="Messages"
            >
              <MessageCircle className="w-5 h-5" />
            </Link>

            {/* Notifications */}
            <Link
              href="/notifications"
              className="relative p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition"
              title="Notifications"
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 w-2 h-2 bg-pink-600 rounded-full" />
              )}
            </Link>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition"
              title="Toggle theme"
            >
              {isDark ? (
                <Sun className="w-5 h-5 text-yellow-500" />
              ) : (
                <Moon className="w-5 h-5" />
              )}
            </button>

            {/* Mobile Menu Button */}
            <button
              className="md:hidden p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
            >
              {isMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>

            {/* User Menu */}
            <div className="relative group hidden md:block">
              <button className="flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition">
                <img
                  src={user?.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${user?.username}`}
                  alt={user?.username}
                  className="w-8 h-8 rounded-full"
                />
                <span className="text-sm">{user?.username}</span>
              </button>

              {/* Dropdown Menu */}
              <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
                <Link
                  href={`/profile/${user?.id}`}
                  className="flex items-center gap-2 px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-t-lg"
                >
                  <User className="w-4 h-4" />
                  <span>Profile</span>
                </Link>
                <Link
                  href="/bookmarks"
                  className="flex items-center gap-2 px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <Bookmark className="w-4 h-4" />
                  <span>Saved Videos</span>
                </Link>
                <Link
                  href="/dashboard"
                  className="flex items-center gap-2 px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <BarChart3 className="w-4 h-4" />
                  <span>Dashboard</span>
                </Link>
                <Link
                  href="/shop/orders"
                  className="flex items-center gap-2 px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <Receipt className="w-4 h-4" />
                  <span>My Orders</span>
                </Link>
                <Link
                  href="/settings/account"
                  className="flex items-center gap-2 px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <Settings className="w-4 h-4" />
                  <span>Settings</span>
                </Link>
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-b-lg text-red-600 dark:text-red-400"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <div className="md:hidden border-t border-gray-200 dark:border-gray-800 py-4 space-y-2">
            <Link
              href="/"
              className="flex items-center gap-2 px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
            >
              <Home className="w-5 h-5" />
              <span>Home</span>
            </Link>
            <Link
              href="/for-you"
              className="flex items-center gap-2 px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
            >
              <Sparkles className="w-5 h-5" />
              <span>For You</span>
            </Link>
            <Link
              href="/search"
              className="flex items-center gap-2 px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
            >
              <Search className="w-5 h-5" />
              <span>Search</span>
            </Link>
            <Link
              href="/discover"
              className="flex items-center gap-2 px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
            >
              <Compass className="w-5 h-5" />
              <span>Discover</span>
            </Link>
            <Link
              href="/create"
              className="flex items-center gap-2 px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
            >
              <Plus className="w-5 h-5" />
              <span>Create</span>
            </Link>
            <Link
              href={`/profile/${user?.id}`}
              className="flex items-center gap-2 px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
            >
              <User className="w-5 h-5" />
              <span>Profile</span>
            </Link>
            <Link
              href="/bookmarks"
              className="flex items-center gap-2 px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
            >
              <Bookmark className="w-5 h-5" />
              <span>Saved Videos</span>
            </Link>
            <Link
              href="/dashboard"
              className="flex items-center gap-2 px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
            >
              <BarChart3 className="w-5 h-5" />
              <span>Dashboard</span>
            </Link>
            <Link
              href="/shop/orders"
              className="flex items-center gap-2 px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
            >
              <Receipt className="w-5 h-5" />
              <span>My Orders</span>
            </Link>
            <Link
              href="/settings/account"
              className="flex items-center gap-2 px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
            >
              <Settings className="w-5 h-5" />
              <span>Settings</span>
            </Link>
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-2 px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded text-red-600"
            >
              <LogOut className="w-5 h-5" />
              <span>Logout</span>
            </button>
          </div>
        )}
      </div>
    </nav>
  );
}
