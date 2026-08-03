'use client';

import { useQuery, useMutation, useQueryClient } from 'react-query';
import { creatorFundApi } from '@/lib/api';
import { Loader2, AlertCircle, DollarSign, CheckCircle2 } from 'lucide-react';

const STATUS_LABEL: Record<string, string> = {
  pending: 'Under review',
  approved: 'Approved',
  rejected: 'Not approved',
};

const STATUS_STYLE: Record<string, string> = {
  pending: 'bg-yellow-50 text-yellow-700 dark:bg-yellow-900/20',
  approved: 'bg-green-50 text-green-700 dark:bg-green-900/20',
  rejected: 'bg-gray-100 text-gray-600 dark:bg-gray-800',
};

export default function CreatorFundPage() {
  const queryClient = useQueryClient();

  const { data: programs, isLoading: programsLoading, error: programsError } = useQuery(
    ['fund-programs'],
    () => creatorFundApi.listPrograms()
  );
  const { data: myApplications, isLoading: applicationsLoading } = useQuery(
    ['my-fund-applications'],
    () => creatorFundApi.getMyApplications()
  );

  const applyMutation = useMutation((programId: string) => creatorFundApi.applyToProgram(programId), {
    onSuccess: () => {
      queryClient.invalidateQueries(['my-fund-applications']);
    },
  });

  const appliedProgramIds = new Set((myApplications || []).map((a) => a.program_id));

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 py-8">
      <div className="max-w-3xl mx-auto px-4">
        <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
          <DollarSign className="w-7 h-7 text-pink-600" />
          Creator Fund
        </h1>
        <p className="text-gray-500 text-sm mb-8">
          Apply to funding programs based on your follower count, published videos, and total views.
        </p>

        {programsLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-pink-600" />
          </div>
        )}

        {!!programsError && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex gap-3 mb-8">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-red-600 dark:text-red-400">Failed to load funding programs</p>
          </div>
        )}

        {!programsLoading && !programsError && (programs || []).length === 0 && (
          <p className="text-gray-500 text-sm text-center py-12">No funding programs are open right now.</p>
        )}

        <div className="space-y-4 mb-10">
          {(programs || []).map((program) => {
            const alreadyApplied = appliedProgramIds.has(program.id);
            return (
              <div key={program.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="font-semibold">{program.name}</h3>
                    {program.description && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{program.description}</p>
                    )}
                    <p className="text-xs text-gray-500 mt-2">
                      Requires {program.min_followers.toLocaleString()}+ followers ·{' '}
                      {program.min_published_videos}+ published videos ·{' '}
                      {program.min_total_views.toLocaleString()}+ total views
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      Award: ${(program.award_amount / 100).toFixed(2)}
                    </p>
                  </div>
                  {alreadyApplied ? (
                    <span className="flex items-center gap-1 text-xs font-semibold text-green-700 dark:text-green-400 whitespace-nowrap">
                      <CheckCircle2 className="w-4 h-4" />
                      Applied
                    </span>
                  ) : (
                    <button
                      onClick={() => applyMutation.mutate(program.id)}
                      disabled={applyMutation.isLoading}
                      className="text-sm font-semibold px-4 py-1.5 rounded-full bg-pink-600 text-white hover:bg-pink-700 disabled:opacity-50 whitespace-nowrap"
                    >
                      Apply
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        <h2 className="text-xl font-bold mb-4">Your Applications</h2>
        {applicationsLoading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-pink-600" />
          </div>
        )}
        {!applicationsLoading && (myApplications || []).length === 0 && (
          <p className="text-gray-500 text-sm">You haven&apos;t applied to any funding programs yet.</p>
        )}
        <div className="space-y-3">
          {(myApplications || []).map((application) => (
            <div
              key={application.id}
              className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex items-center justify-between"
            >
              <div>
                <p className="text-sm">
                  {application.followers_count.toLocaleString()} followers ·{' '}
                  {application.published_videos_count} videos ·{' '}
                  {application.total_views_count.toLocaleString()} views at time of application
                </p>
                {application.status === 'approved' && (
                  <p className="text-xs text-green-700 dark:text-green-400 mt-1">
                    Awarded ${((application.awarded_amount || 0) / 100).toFixed(2)}
                  </p>
                )}
                {application.decision_reason && (
                  <p className="text-xs text-gray-500 mt-1">{application.decision_reason}</p>
                )}
              </div>
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full whitespace-nowrap ${STATUS_STYLE[application.status]}`}>
                {STATUS_LABEL[application.status]}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
