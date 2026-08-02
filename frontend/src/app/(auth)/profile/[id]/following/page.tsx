'use client';

import FollowList from '@/components/features/FollowList';

interface FollowingPageProps {
  params: { id: string };
}

export default function FollowingPage({ params }: FollowingPageProps) {
  return <FollowList userId={params.id} mode="following" />;
}
