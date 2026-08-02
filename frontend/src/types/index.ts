// User types - field names match the backend's actual wire format (snake_case)
// rather than an idealized camelCase shape, since there is no transform layer.

// Matches UserPublicProfile: minimal info shown on video authors, follower lists, etc.
export interface PublicUser {
  id: string;
  username: string;
  avatar_url: string | null;
  is_verified: boolean;
  is_creator: boolean;
}

// Matches UserResponse / UserFullProfile: full profile, includes email.
export interface User {
  id: string;
  email: string;
  username: string;
  first_name: string | null;
  last_name: string | null;
  bio: string | null;
  avatar_url: string | null;
  cover_url: string | null;
  website: string | null;
  is_creator: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface ProfileStatistics {
  followers_count: number;
  following_count: number;
  videos_count: number;
  likes_count: number;
  total_views: number;
}

// Matches ProfileResponse from GET /api/profiles/{id}
export interface ProfileDetail {
  user: User;
  statistics: ProfileStatistics;
  is_following: boolean;
  is_blocked: boolean;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

// Video types - matches VideoDetailResponse
export interface Video {
  id: string;
  user_id: string;
  user: PublicUser;
  title: string | null;
  description: string | null;
  video_url: string;
  thumbnail_url: string | null;
  duration: number | null;
  hashtags: string | null;
  is_public: boolean;
  views_count: number;
  likes_count: number;
  comments_count: number;
  shares_count: number;
  bookmarks_count: number;
  is_liked: boolean;
  is_bookmarked: boolean;
  allow_comments: boolean;
  allow_duets: boolean;
  allow_stitches: boolean;
  remix_type: 'duet' | 'stitch' | null;
  original_video: {
    id: string;
    title: string | null;
    thumbnail_url: string | null;
    user: PublicUser;
  } | null;
  music: {
    id: string;
    sound_title: string;
    artist: string | null;
  } | null;
  created_at: string;
  published_at: string | null;
}

// Comment types
export interface Comment {
  id: string;
  video_id: string;
  user_id: string;
  user: PublicUser;
  parent_comment_id: string | null;
  content: string;
  likes_count: number;
  replies_count: number;
  is_pinned: boolean;
  is_liked: boolean;
  created_at: string;
  updated_at: string;
}

// Notification types
export interface Notification {
  id: string;
  userId: string;
  actorId: string;
  type: 'like' | 'comment' | 'follow' | 'mention' | 'message';
  targetId: string;
  isRead: boolean;
  createdAt: string;
}

// Message types
export interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  content: string;
  is_read: boolean;
  created_at: string;
}

export interface Conversation {
  id: string;
  other_user: PublicUser;
  last_message: Message | null;
  unread_count: number;
  updated_at: string;
}

// API Response types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
  cursor?: string;
  hasMore?: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  cursor?: string;
  hasMore: boolean;
}

// Feed types - matches FeedResponse. Pagination is offset-based in practice;
// `cursor` exists on the wire but the backend never populates it (always null).
export interface FeedResponse {
  videos: Video[];
  cursor: string | null;
  total: number | null;
}
