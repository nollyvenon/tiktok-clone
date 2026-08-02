'use client';

import FollowList from '@/components/features/FollowList';

interface FollowersPageProps {
  params: { id: string };
}

export default function FollowersPage({ params }: FollowersPageProps) {
  return <FollowList userId={params.id} mode="followers" />;
}
