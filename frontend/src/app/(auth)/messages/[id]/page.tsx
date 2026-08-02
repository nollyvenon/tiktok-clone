'use client';

import { useEffect, useRef, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import Link from 'next/link';
import { messageApi } from '@/lib/api';
import { useAuthStore } from '@/stores/authStore';
import { Loader2, ArrowLeft, Send } from 'lucide-react';

interface MessagesDetailPageProps {
  params: { id: string };
}

// No WebSocket transport exists in this app yet, so new messages are
// picked up via short polling rather than a live push - matches the
// notification system's known gap (no real-time delivery infra yet).
const POLL_INTERVAL_MS = 4000;

export default function MessageThreadPage({ params }: MessagesDetailPageProps) {
  const conversationId = params.id;
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [content, setContent] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: conversationsData } = useQuery(['conversations'], () =>
    messageApi.getConversations(50, 0)
  );
  const conversation = conversationsData?.conversations.find((c) => c.id === conversationId);

  const messagesQuery = useQuery(
    ['messages', conversationId],
    () => messageApi.getMessages(conversationId, 50, 0),
    { refetchInterval: POLL_INTERVAL_MS }
  );

  const sendMutation = useMutation(
    (text: string) => messageApi.sendMessage(conversationId, text),
    {
      onSuccess: () => {
        setContent('');
        queryClient.invalidateQueries(['messages', conversationId]);
        queryClient.invalidateQueries(['conversations']);
      },
    }
  );

  useEffect(() => {
    messageApi.markRead(conversationId).then(() => {
      queryClient.invalidateQueries(['conversations']);
    });
  }, [conversationId, queryClient]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messagesQuery.data]);

  const messages = messagesQuery.data?.messages || [];

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 flex flex-col">
      <div className="border-b border-gray-200 dark:border-gray-800 p-4 flex items-center gap-3">
        <Link
          href="/messages"
          className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        {conversation && (
          <>
            <img
              src={
                conversation.other_user.avatar_url ||
                `https://api.dicebear.com/7.x/avataaars/svg?seed=${conversation.other_user.username}`
              }
              alt={conversation.other_user.username}
              className="w-9 h-9 rounded-full"
            />
            <span className="font-semibold">@{conversation.other_user.username}</span>
          </>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 max-w-2xl w-full mx-auto">
        {messagesQuery.isLoading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-6 h-6 animate-spin text-pink-600" />
          </div>
        ) : messages.length === 0 ? (
          <p className="text-center text-gray-500 text-sm py-16">
            No messages yet. Say hello!
          </p>
        ) : (
          <div className="space-y-2">
            {messages.map((message) => {
              const isOwn = message.sender_id === user?.id;
              return (
                <div key={message.id} className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}>
                  <div
                    className={`max-w-xs px-4 py-2 rounded-2xl text-sm ${
                      isOwn
                        ? 'bg-pink-600 text-white rounded-br-sm'
                        : 'bg-gray-100 dark:bg-gray-800 rounded-bl-sm'
                    }`}
                  >
                    {message.content}
                  </div>
                </div>
              );
            })}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <div className="border-t border-gray-200 dark:border-gray-800 p-4">
        <div className="max-w-2xl mx-auto flex gap-2">
          <input
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Type a message..."
            className="flex-1 px-4 py-2 rounded-full border border-gray-300 dark:border-gray-700 dark:bg-gray-800 text-sm"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && content.trim()) sendMutation.mutate(content);
            }}
          />
          <button
            onClick={() => sendMutation.mutate(content)}
            disabled={sendMutation.isLoading || !content.trim()}
            className="p-2 rounded-full bg-pink-600 hover:bg-pink-700 text-white disabled:opacity-50 transition"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
