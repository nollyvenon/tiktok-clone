'use client';

import { Suspense, useState, useCallback, useEffect } from 'react';
import { useQuery } from 'react-query';
import { useSearchParams } from 'next/navigation';
import { searchApi } from '@/lib/api';
import { VideoCard } from '@/components/features/VideoCard';
import { Search, Loader2, AlertCircle } from 'lucide-react';
import Link from 'next/link';

type SearchType = 'videos' | 'users';

function SearchPageContent() {
  const searchParams = useSearchParams();
  const [query, setQuery] = useState(searchParams.get('q') ?? '');
  const [searchType, setSearchType] = useState<SearchType>('videos');
  const [debouncedQuery, setDebouncedQuery] = useState(searchParams.get('q') ?? '');

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 500);
    return () => clearTimeout(timer);
  }, [query]);

  const handleSearch = useCallback((value: string) => {
    setQuery(value);
  }, []);

  const videoQuery = useQuery(
    ['search', 'videos', debouncedQuery],
    () => searchApi.searchVideos(debouncedQuery),
    { enabled: debouncedQuery.length > 0 && searchType === 'videos' }
  );

  const userQuery = useQuery(
    ['search', 'users', debouncedQuery],
    () => searchApi.searchCreators(debouncedQuery),
    { enabled: debouncedQuery.length > 0 && searchType === 'users' }
  );

  const { isLoading, error } = searchType === 'videos' ? videoQuery : userQuery;
  const videoResults = videoQuery.data?.results || [];
  const userResults = userQuery.data?.results || [];
  const results = searchType === 'videos' ? videoResults : userResults;

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 pt-4">
      <div className="max-w-7xl mx-auto px-4">
        {/* Search Input */}
        <div className="mb-8 sticky top-16 bg-white dark:bg-gray-900 py-4 z-40">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder="Search videos or creators..."
              className="w-full pl-12 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-full bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-pink-600"
              autoFocus
            />
          </div>
        </div>

        {/* Filters */}
        {debouncedQuery && (
          <div className="flex gap-2 mb-8">
            {(['videos', 'users'] as const).map((type) => (
              <button
                key={type}
                onClick={() => setSearchType(type)}
                className={`px-4 py-2 rounded-full font-semibold whitespace-nowrap transition ${
                  searchType === type
                    ? 'bg-pink-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700'
                }`}
              >
                {type === 'videos' ? 'Videos' : 'Creators'}
              </button>
            ))}
          </div>
        )}

        {/* Results */}
        {!debouncedQuery ? (
          <div className="text-center py-16">
            <Search className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-700 mb-4" />
            <h2 className="text-2xl font-bold mb-2">Start searching</h2>
            <p className="text-gray-600 dark:text-gray-400">
              Find videos and creators
            </p>
          </div>
        ) : isLoading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
          </div>
        ) : error ? (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-red-600 dark:text-red-400">
              {error instanceof Error ? error.message : 'Search failed'}
            </p>
          </div>
        ) : results.length === 0 ? (
          <div className="text-center py-16">
            <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
              <Search className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-semibold mb-1">No results</h3>
            <p className="text-gray-600 dark:text-gray-400">
              No results found for &quot;{debouncedQuery}&quot;
            </p>
          </div>
        ) : searchType === 'videos' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pb-8">
            {videoResults.map((video) => (
              <VideoCard key={video.id} video={video} />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 pb-8">
            {userResults.map((user) => (
              <Link
                key={user.id}
                href={`/profile/${user.id}`}
                className="bg-white dark:bg-gray-800 rounded-lg overflow-hidden hover:shadow-lg transition-shadow"
              >
                <div className="aspect-square bg-gradient-to-br from-pink-400 to-pink-600" />
                <div className="p-4">
                  <img
                    src={user.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${user.username}`}
                    alt={user.username}
                    className="w-12 h-12 rounded-full mb-2 -mt-8 border-2 border-white dark:border-gray-800"
                  />
                  <p className="font-semibold">@{user.username}</p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
        </div>
      }
    >
      <SearchPageContent />
    </Suspense>
  );
}
