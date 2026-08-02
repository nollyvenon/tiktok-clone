'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { commentApi } from '@/lib/api';
import { useAuthStore } from '@/stores/authStore';
import { Heart, Pin, Pencil, Trash2, MessageCircle, Flag } from 'lucide-react';
import type { Comment } from '@/types';
import ReportModal from './ReportModal';

interface CommentSectionProps {
  videoId: string;
  videoOwnerId: string;
}

function timeAgo(iso: string): string {
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h`;
  const days = Math.floor(hours / 24);
  return `${days}d`;
}

function CommentRow({
  comment,
  videoId,
  videoOwnerId,
  currentUserId,
  isReply = false,
}: {
  comment: Comment;
  videoId: string;
  videoOwnerId: string;
  currentUserId: string | undefined;
  isReply?: boolean;
}) {
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const [editContent, setEditContent] = useState(comment.content);
  const [isReplying, setIsReplying] = useState(false);
  const [replyContent, setReplyContent] = useState('');
  const [showReplies, setShowReplies] = useState(false);

  const isOwnComment = currentUserId === comment.user_id;
  const isVideoOwner = currentUserId === videoOwnerId;

  const repliesQuery = useQuery(
    ['comment-replies', comment.id],
    () => commentApi.getReplies(comment.id),
    { enabled: showReplies }
  );

  const likeMutation = useMutation(() => commentApi.likeComment(comment.id), {
    onSuccess: () => {
      queryClient.invalidateQueries(['comments', videoId]);
      queryClient.invalidateQueries(['comment-replies']);
    },
  });

  const pinMutation = useMutation(() => commentApi.pinComment(comment.id), {
    onSuccess: () => queryClient.invalidateQueries(['comments', videoId]),
  });

  const updateMutation = useMutation(
    (content: string) => commentApi.updateComment(comment.id, content),
    {
      onSuccess: () => {
        setIsEditing(false);
        queryClient.invalidateQueries(['comments', videoId]);
        queryClient.invalidateQueries(['comment-replies']);
      },
    }
  );

  const deleteMutation = useMutation(() => commentApi.deleteComment(comment.id), {
    onSuccess: () => {
      queryClient.invalidateQueries(['comments', videoId]);
      queryClient.invalidateQueries(['comment-replies']);
    },
  });

  const replyMutation = useMutation(
    (content: string) => commentApi.createComment(videoId, content, comment.id),
    {
      onSuccess: () => {
        setReplyContent('');
        setIsReplying(false);
        setShowReplies(true);
        queryClient.invalidateQueries(['comments', videoId]);
        queryClient.invalidateQueries(['comment-replies', comment.id]);
      },
    }
  );

  return (
    <div className={isReply ? 'ml-10 mt-3' : 'mb-4'}>
      <div className="flex gap-3">
        <img
          src={
            comment.user.avatar_url ||
            `https://api.dicebear.com/7.x/avataaars/svg?seed=${comment.user.username}`
          }
          alt={comment.user.username}
          className="w-8 h-8 rounded-full flex-shrink-0"
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-sm">@{comment.user.username}</span>
            {comment.is_pinned && (
              <span className="flex items-center gap-1 text-xs text-gray-500">
                <Pin className="w-3 h-3" /> Pinned
              </span>
            )}
            <span className="text-xs text-gray-500">{timeAgo(comment.created_at)}</span>
          </div>

          {isEditing ? (
            <div className="mt-1 flex gap-2">
              <input
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="flex-1 px-3 py-1 rounded-lg border border-gray-300 dark:border-gray-700 dark:bg-gray-800 text-sm"
              />
              <button
                onClick={() => updateMutation.mutate(editContent)}
                disabled={updateMutation.isLoading || !editContent.trim()}
                className="text-sm text-pink-600 font-semibold"
              >
                Save
              </button>
              <button onClick={() => setIsEditing(false)} className="text-sm text-gray-500">
                Cancel
              </button>
            </div>
          ) : (
            <p className="text-sm mt-0.5">{comment.content}</p>
          )}

          <div className="flex items-center gap-4 mt-1">
            <button
              onClick={() => likeMutation.mutate()}
              disabled={likeMutation.isLoading}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-red-600"
            >
              <Heart className={`w-3.5 h-3.5 ${comment.is_liked ? 'fill-red-600 text-red-600' : ''}`} />
              {comment.likes_count > 0 && comment.likes_count}
            </button>
            {!isReply && (
              <button
                onClick={() => setIsReplying((v) => !v)}
                className="text-xs text-gray-500 hover:text-gray-800 dark:hover:text-gray-200"
              >
                Reply
              </button>
            )}
            {isOwnComment && !isEditing && (
              <button
                onClick={() => setIsEditing(true)}
                className="text-xs text-gray-500 hover:text-gray-800 dark:hover:text-gray-200"
              >
                <Pencil className="w-3.5 h-3.5" />
              </button>
            )}
            {(isOwnComment || isVideoOwner) && (
              <button
                onClick={() => deleteMutation.mutate()}
                disabled={deleteMutation.isLoading}
                className="text-xs text-gray-500 hover:text-red-600"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            )}
            {!isOwnComment && (
              <button
                onClick={() => setShowReportModal(true)}
                className="text-xs text-gray-500 hover:text-red-600"
              >
                <Flag className="w-3.5 h-3.5" />
              </button>
            )}
            {!isReply && isVideoOwner && (
              <button
                onClick={() => pinMutation.mutate()}
                disabled={pinMutation.isLoading}
                className="text-xs text-gray-500 hover:text-gray-800 dark:hover:text-gray-200"
              >
                {comment.is_pinned ? 'Unpin' : 'Pin'}
              </button>
            )}
            {!isReply && comment.replies_count > 0 && (
              <button
                onClick={() => setShowReplies((v) => !v)}
                className="text-xs text-pink-600 font-semibold"
              >
                {showReplies ? 'Hide' : 'View'} {comment.replies_count}{' '}
                {comment.replies_count === 1 ? 'reply' : 'replies'}
              </button>
            )}
          </div>

          {isReplying && (
            <div className="mt-2 flex gap-2">
              <input
                value={replyContent}
                onChange={(e) => setReplyContent(e.target.value)}
                placeholder={`Reply to @${comment.user.username}`}
                className="flex-1 px-3 py-1 rounded-lg border border-gray-300 dark:border-gray-700 dark:bg-gray-800 text-sm"
              />
              <button
                onClick={() => replyMutation.mutate(replyContent)}
                disabled={replyMutation.isLoading || !replyContent.trim()}
                className="text-sm text-pink-600 font-semibold"
              >
                Post
              </button>
            </div>
          )}

          {showReplies && repliesQuery.data && (
            <div>
              {repliesQuery.data.comments.map((reply) => (
                <CommentRow
                  key={reply.id}
                  comment={reply}
                  videoId={videoId}
                  videoOwnerId={videoOwnerId}
                  currentUserId={currentUserId}
                  isReply
                />
              ))}
            </div>
          )}
          {showReportModal && (
            <ReportModal
              contentType="comment"
              contentId={comment.id}
              onClose={() => setShowReportModal(false)}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default function CommentSection({ videoId, videoOwnerId }: CommentSectionProps) {
  const { user } = useAuthStore();
  const [newComment, setNewComment] = useState('');
  const queryClient = useQueryClient();

  const commentsQuery = useQuery(['comments', videoId], () => commentApi.getComments(videoId));

  const createMutation = useMutation(
    (content: string) => commentApi.createComment(videoId, content),
    {
      onSuccess: () => {
        setNewComment('');
        queryClient.invalidateQueries(['comments', videoId]);
      },
    }
  );

  return (
    <div className="mb-8">
      <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
        <MessageCircle className="w-5 h-5" />
        Comments {commentsQuery.data && `(${commentsQuery.data.total})`}
      </h2>

      {user && (
        <div className="flex gap-2 mb-6">
          <input
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Add a comment..."
            className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 dark:bg-gray-800 text-sm"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && newComment.trim()) createMutation.mutate(newComment);
            }}
          />
          <button
            onClick={() => createMutation.mutate(newComment)}
            disabled={createMutation.isLoading || !newComment.trim()}
            className="px-4 py-2 rounded-lg bg-pink-600 text-white font-semibold text-sm disabled:opacity-50"
          >
            Post
          </button>
        </div>
      )}

      {commentsQuery.isLoading && (
        <p className="text-sm text-gray-500">Loading comments...</p>
      )}

      {commentsQuery.data && commentsQuery.data.comments.length === 0 && (
        <p className="text-gray-600 dark:text-gray-400 text-sm">
          No comments yet. Be the first to comment!
        </p>
      )}

      {commentsQuery.data?.comments.map((comment) => (
        <CommentRow
          key={comment.id}
          comment={comment}
          videoId={videoId}
          videoOwnerId={videoOwnerId}
          currentUserId={user?.id}
        />
      ))}
    </div>
  );
}
