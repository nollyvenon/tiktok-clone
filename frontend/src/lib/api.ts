import axios, { AxiosInstance, AxiosError } from 'axios';
import type { ApiResponse, AuthResponse, FeedResponse, Video, PublicUser, Comment, User, Notification, Message, Conversation } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const createClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Add token to requests
  client.interceptors.request.use((config) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  // Handle errors
  client.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
      if (error.response?.status === 401) {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('token');
          window.location.href = '/login';
        }
      }
      return Promise.reject(error);
    }
  );

  return client;
};

const client = createClient();

// Auth endpoints
export const authApi = {
  login: async (email: string, password: string) => {
    const res = await client.post<AuthResponse>('/api/auth/login', { email, password });
    return res.data;
  },

  register: async (email: string, username: string, password: string) => {
    const res = await client.post<AuthResponse>('/api/auth/register', { email, username, password });
    return res.data;
  },

  logout: async (everywhere = false) => {
    await client.post('/api/auth/logout', null, { params: { everywhere } });
  },

  getCurrentUser: async () => {
    const res = await client.get<User>('/api/auth/me');
    return res.data;
  },

  refreshToken: async (refreshToken: string) => {
    const res = await client.post('/api/auth/refresh', { refresh_token: refreshToken });
    return res.data;
  },

  changePassword: async (currentPassword: string, newPassword: string, confirmPassword: string) => {
    await client.post('/api/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
      confirm_password: confirmPassword,
    });
  },

  exportMyData: async () => {
    const res = await client.get('/api/auth/me/export');
    return res.data;
  },

  deleteAccount: async (password: string) => {
    await client.delete('/api/auth/me', { data: { password } });
  },

  requestPasswordReset: async (email: string) => {
    await client.post('/api/auth/password-reset', { email });
  },

  resetPassword: async (token: string, newPassword: string, confirmPassword: string) => {
    await client.post('/api/auth/password-reset/confirm', {
      token,
      new_password: newPassword,
      confirm_password: confirmPassword,
    });
  },

  listSessions: async () => {
    const res = await client.get('/api/auth/sessions');
    return res.data as { sessions: Array<{
      id: string; device_id: string | null; device_name: string | null;
      ip_address: string | null; is_current: boolean; created_at: string; last_activity: string;
    }> };
  },

  revokeSession: async (sessionId: string) => {
    await client.delete(`/api/auth/sessions/${sessionId}`);
  },

  sendOTP: async (phoneNumber?: string, email?: string) => {
    const res = await client.post('/api/auth/otp/send', {
      phone_number: phoneNumber,
      email,
    });
    return res.data;
  },

  verifyOTP: async (code: string, phoneNumber?: string, email?: string) => {
    const res = await client.post('/api/auth/otp/verify', {
      code,
      phone_number: phoneNumber,
      email,
    });
    return res.data;
  },

  setup2FA: async () => {
    const res = await client.post('/api/auth/2fa/setup');
    return res.data;
  },

  verify2FA: async (code: string) => {
    const res = await client.post('/api/auth/2fa/verify', { code });
    return res.data;
  },

  disable2FA: async () => {
    const res = await client.post('/api/auth/2fa/disable');
    return res.data;
  },
};

// Profile endpoints
export const profileApi = {
  getProfile: async (userId: string) => {
    const res = await client.get(`/api/profiles/${userId}`);
    return res.data;
  },

  getProfileByUsername: async (username: string) => {
    const res = await client.get(`/api/profiles/username/${username}`);
    return res.data;
  },

  updateProfile: async (data: {
    first_name?: string;
    last_name?: string;
    bio?: string;
    avatar_url?: string;
    cover_url?: string;
    website?: string;
  }) => {
    const res = await client.put('/api/profiles/me', data);
    return res.data;
  },

  followUser: async (userId: string) => {
    const res = await client.post(`/api/profiles/${userId}/follow`);
    return res.data;
  },

  getFollowers: async (userId: string, limit = 20, offset = 0) => {
    const res = await client.get<FollowListResult>(`/api/profiles/${userId}/followers`, {
      params: { limit, offset },
    });
    return res.data;
  },

  getFollowing: async (userId: string, limit = 20, offset = 0) => {
    const res = await client.get<FollowListResult>(`/api/profiles/${userId}/following`, {
      params: { limit, offset },
    });
    return res.data;
  },

  blockUser: async (userId: string) => {
    const res = await client.post<{ is_blocked: boolean; message: string }>(
      `/api/profiles/${userId}/block`
    );
    return res.data;
  },

  getBlockedUsers: async () => {
    const res = await client.get<{ users: PublicUser[]; total: number }>('/api/profiles/me/blocked');
    return res.data;
  },
};

export interface FollowListUser {
  id: string;
  username: string;
  avatar_url: string | null;
  is_verified: boolean;
  is_creator: boolean;
  is_following: boolean;
  is_followed_by: boolean;
}

export interface FollowListResult {
  users: FollowListUser[];
  total: number;
}

// Upload & Draft endpoints
export const uploadApi = {
  getPresignedUrl: async (filename: string, fileSize: number, mimeType: string) => {
    const res = await client.post('/api/uploads/presigned-url', {
      filename,
      file_size: fileSize,
      mime_type: mimeType,
    });
    return res.data as { upload_id: string; presigned_url: string; expires_in: number };
  },

  completeUpload: async (
    uploadId: string,
    processedVideoUrl: string,
    thumbnailUrl: string,
    duration: number
  ) => {
    const res = await client.post(
      `/api/uploads/${uploadId}/complete`,
      null,
      {
        params: {
          processed_video_url: processedVideoUrl,
          thumbnail_url: thumbnailUrl,
          duration,
        },
      }
    );
    return res.data;
  },

  createDraft: async (
    data: {
      title?: string;
      description?: string;
      hashtags?: string;
      is_public?: boolean;
      original_video_id?: string;
      remix_type?: 'duet' | 'stitch';
    },
    uploadId?: string
  ) => {
    const res = await client.post('/api/uploads/drafts', data, {
      params: uploadId ? { upload_id: uploadId } : undefined,
    });
    return res.data;
  },

  getDraft: async (draftId: string) => {
    const res = await client.get(`/api/uploads/drafts/${draftId}`);
    return res.data;
  },

  updateDraft: async (draftId: string, data: Record<string, unknown>) => {
    const res = await client.put(`/api/uploads/drafts/${draftId}`, data);
    return res.data;
  },

  deleteDraft: async (draftId: string) => {
    await client.delete(`/api/uploads/drafts/${draftId}`);
  },

  getUserDrafts: async (limit = 20, offset = 0) => {
    const res = await client.get('/api/uploads/drafts', { params: { limit, offset } });
    return res.data as { drafts: unknown[]; total: number };
  },

  publishDraft: async (draftId: string) => {
    const res = await client.post(`/api/uploads/drafts/${draftId}/publish`);
    return res.data as { message: string; video_id: string; status: string };
  },

  scheduleDraft: async (draftId: string, publishAt: string) => {
    const res = await client.post(`/api/uploads/drafts/${draftId}/schedule`, null, {
      params: { publish_at: publishAt },
    });
    return res.data;
  },
};

export interface Segment {
  id: string;
  start_time: number;
  end_time: number;
  order: number;
  content_type: string;
  content_url: string;
  effects: string[] | null;
  transition_type: string | null;
  transition_duration: number;
  volume: number;
  muted: boolean;
  created_at: string;
}

export interface TextOverlay {
  id: string;
  text: string;
  font_family: string;
  font_size: number;
  color: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface Sticker {
  id: string;
  sticker_url: string;
  sticker_type: string;
  x: number;
  y: number;
  width: number;
  height: number;
  rotation: number;
}

export interface EditorState {
  draft_id: string;
  segments: Segment[];
  text_overlays: TextOverlay[];
  stickers: Sticker[];
  total_duration: number;
}

// Editor endpoints (Module 5) - timeline-based segment editing
export const editorApi = {
  getEditorState: async (draftId: string) => {
    const res = await client.get<EditorState>(`/api/editor/drafts/${draftId}/state`);
    return res.data;
  },

  addSegment: async (
    draftId: string,
    data: {
      start_time: number;
      end_time: number;
      content_type: string;
      content_url: string;
      volume?: number;
      muted?: boolean;
    }
  ) => {
    const res = await client.post<Segment>(`/api/editor/drafts/${draftId}/segments`, data);
    return res.data;
  },

  deleteSegment: async (segmentId: string) => {
    await client.delete(`/api/editor/segments/${segmentId}`);
  },

  reorderSegments: async (draftId: string, segmentIds: string[]) => {
    await client.post(`/api/editor/drafts/${draftId}/reorder-segments`, null, {
      params: { segment_ids: segmentIds },
      paramsSerializer: { indexes: null },
    });
  },

  applyEffect: async (segmentId: string, effectName: string) => {
    const res = await client.post<Segment>(`/api/editor/segments/${segmentId}/effects/${effectName}`);
    return res.data;
  },

  trimSegment: async (segmentId: string, startTime: number, endTime: number) => {
    const res = await client.post<Segment>(`/api/editor/segments/${segmentId}/trim`, null, {
      params: { start_time: startTime, end_time: endTime },
    });
    return res.data;
  },

  adjustSpeed: async (segmentId: string, speed: number) => {
    const res = await client.post<Segment>(`/api/editor/segments/${segmentId}/speed`, null, {
      params: { speed },
    });
    return res.data;
  },

  adjustVolume: async (segmentId: string, volume: number) => {
    const res = await client.post<Segment>(`/api/editor/segments/${segmentId}/volume`, null, {
      params: { volume },
    });
    return res.data;
  },

  muteSegment: async (segmentId: string, muted: boolean) => {
    const res = await client.post<Segment>(`/api/editor/segments/${segmentId}/mute`, null, {
      params: { muted },
    });
    return res.data;
  },

  addTextOverlay: async (
    segmentId: string,
    data: { text: string; x: number; y: number; width: number; height: number }
  ) => {
    const res = await client.post<TextOverlay>(`/api/editor/segments/${segmentId}/overlays`, data);
    return res.data;
  },

  deleteTextOverlay: async (overlayId: string) => {
    await client.delete(`/api/editor/overlays/${overlayId}`);
  },

  addSticker: async (
    segmentId: string,
    data: { sticker_url: string; sticker_type: string; x: number; y: number; width: number; height: number }
  ) => {
    const res = await client.post<Sticker>(`/api/editor/segments/${segmentId}/stickers`, data);
    return res.data;
  },

  getStickers: async (segmentId: string) => {
    const res = await client.get(`/api/editor/segments/${segmentId}/stickers`);
    return res.data as { stickers: Sticker[]; total: number };
  },

  deleteSticker: async (stickerId: string) => {
    await client.delete(`/api/editor/stickers/${stickerId}`);
  },

  exportVideo: async (draftId: string, quality = '1080p', format = 'mp4') => {
    const res = await client.post(`/api/editor/drafts/${draftId}/export`, null, {
      params: { quality, format },
    });
    return res.data as {
      export_id: string; draft_id: string; quality: string; format: string;
      status: string; progress: number; created_at: string;
    };
  },
};

export interface AICreditsInfo {
  total_credits: number;
  available_credits: number;
  used_credits: number;
  monthly_limit: number;
  renewal_date: string | null;
}

// AI Creator Studio endpoints (Module 6)
export interface FilterPreset {
  id: string;
  name: string;
  label: string;
  thumbnail_url: string | null;
  brightness: number;
  contrast: number;
  saturation: number;
  hue: number;
  temperature: number;
}

export interface AgentStep {
  operation: string;
  params: Record<string, unknown>;
}

export interface AIAgent {
  id: string;
  name: string;
  label: string;
  description: string | null;
  steps: AgentStep[];
}

export interface AgentStepResult {
  operation: string;
  status: string;
  credits_used: number;
  result_id: string | null;
  error: string | null;
}

export interface AgentExecution {
  id: string;
  agent_id: string;
  segment_id: string;
  status: 'running' | 'completed' | 'failed';
  steps_log: AgentStepResult[];
  total_credits_used: number;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
}

export const aiApi = {
  getCredits: async () => {
    const res = await client.get<AICreditsInfo>('/api/ai/credits');
    return res.data;
  },

  removeBackground: async (data: {
    segment_id: string;
    mode: 'blur' | 'remove' | 'replace' | 'green_screen';
    blur_level?: number;
    background_url?: string;
    background_type?: string;
  }) => {
    const res = await client.post('/api/ai/background-removal', data);
    return res.data;
  },

  generateVoiceover: async (data: {
    segment_id: string;
    text: string;
    language?: string;
    voice_id: string;
    speed?: number;
    pitch?: number;
    volume?: number;
  }) => {
    const res = await client.post('/api/ai/voiceover', data);
    return res.data;
  },

  generateCaptions: async (data: {
    segment_id: string;
    language?: string;
    style?: string;
    position?: string;
  }) => {
    const res = await client.post('/api/ai/captions', data);
    return res.data;
  },

  applyColorCorrection: async (data: {
    segment_id: string;
    method?: string;
    preset_name?: string;
    brightness?: number;
    contrast?: number;
    saturation?: number;
    hue?: number;
    temperature?: number;
  }) => {
    const res = await client.post('/api/ai/color-correction', data);
    return res.data;
  },

  getFilterPresets: async () => {
    const res = await client.get<{ presets: FilterPreset[] }>('/api/ai/filters/presets');
    return res.data.presets;
  },

  getAgents: async () => {
    const res = await client.get<{ agents: AIAgent[] }>('/api/ai/agents');
    return res.data.agents;
  },

  executeAgent: async (agentId: string, segmentId: string) => {
    const res = await client.post<AgentExecution>(`/api/ai/agents/${agentId}/execute`, null, {
      params: { segment_id: segmentId },
    });
    return res.data;
  },

  getMyAgentExecutions: async () => {
    const res = await client.get<{ executions: AgentExecution[] }>('/api/ai/agents/executions');
    return res.data.executions;
  },

  getFrameSuggestions: async (segmentId: string, targetAspectRatio = '9:16') => {
    const res = await client.post('/api/ai/smart-frame', null, {
      params: { segment_id: segmentId, target_aspect_ratio: targetAspectRatio },
    });
    return res.data;
  },

  getSoundRecommendations: async (params?: { category?: string; mood?: string; region?: string }) => {
    const res = await client.get<SoundRecommendationsListResponse>(
      '/api/ai/sounds/recommendations',
      { params }
    );
    return res.data;
  },

  getTrendingSounds: async (region = 'US', limit = 10) => {
    const res = await client.get<SoundRecommendationsListResponse>('/api/ai/sounds/trending', {
      params: { region, limit },
    });
    return res.data;
  },

  createSound: async (data: {
    sound_url: string;
    sound_title: string;
    artist?: string;
    category: string;
    mood?: string;
    genre?: string;
    region?: string;
    duration?: number;
    license_type?: string;
    credit_required?: string;
  }) => {
    const res = await client.post<SoundRecommendation>('/api/ai/sounds', data);
    return res.data;
  },

  getVideosUsingSound: async (soundId: string, limit = 20, offset = 0) => {
    const res = await client.get<FeedResponse>(`/api/ai/sounds/${soundId}/videos`, {
      params: { limit, offset },
    });
    return res.data;
  },
};

export interface SoundRecommendation {
  id: string;
  sound_url: string;
  sound_title: string;
  artist: string | null;
  category: string;
  mood: string | null;
  duration: number | null;
  is_trending: boolean;
}

export interface SoundRecommendationsListResponse {
  sounds: SoundRecommendation[];
  total: number;
  category: string;
  region: string;
}

// Video endpoints - matches the real /api/videos routes: offset-based
// pagination (the `cursor` field is a backend TODO, always null in practice),
// and single toggle endpoints for like/bookmark rather than separate
// like+unlike / bookmark+unbookmark pairs.
export const videoApi = {
  getFeed: async (feedType: 'for_you' | 'following' = 'for_you', offset = 0, limit = 10) => {
    const res = await client.get<FeedResponse>('/api/videos/feed', {
      params: { feed_type: feedType, offset, limit },
    });
    return res.data;
  },

  getVideo: async (id: string) => {
    const res = await client.get<Video>(`/api/videos/${id}`);
    return res.data;
  },

  updateVideo: async (id: string, data: Partial<Video>) => {
    const res = await client.put<Video>(`/api/videos/${id}`, data);
    return res.data;
  },

  deleteVideo: async (id: string) => {
    await client.delete(`/api/videos/${id}`);
  },

  /** Toggles like state; returns the resulting is_liked/likes_count. */
  toggleLike: async (id: string) => {
    const res = await client.post<{ is_liked: boolean; likes_count: number }>(
      `/api/videos/${id}/like`
    );
    return res.data;
  },

  /** Toggles bookmark state; returns the resulting is_bookmarked/bookmarks_count. */
  toggleBookmark: async (id: string) => {
    const res = await client.post<{ is_bookmarked: boolean; bookmarks_count: number }>(
      `/api/videos/${id}/bookmark`
    );
    return res.data;
  },

  trackView: async (id: string) => {
    await client.post(`/api/videos/${id}/view`);
  },

  search: async (query: string, limit = 20, offset = 0) => {
    const res = await client.get<FeedResponse>('/api/videos/search', {
      params: { q: query, limit, offset },
    });
    return res.data;
  },

  getTrending: async (limit = 20, offset = 0) => {
    const res = await client.get<FeedResponse>('/api/videos/search/trending', {
      params: { limit, offset },
    });
    return res.data;
  },

  getUserVideos: async (userId: string, limit = 20, offset = 0) => {
    const res = await client.get<FeedResponse>(`/api/videos/user/${userId}/videos`, {
      params: { limit, offset },
    });
    return res.data;
  },

  getBookmarks: async (limit = 20, offset = 0) => {
    const res = await client.get<FeedResponse>('/api/videos/bookmarks', {
      params: { limit, offset },
    });
    return res.data;
  },

  getRemixes: async (videoId: string, remixType?: 'duet' | 'stitch', limit = 20, offset = 0) => {
    const res = await client.get<FeedResponse>(`/api/videos/${videoId}/remixes`, {
      params: { remix_type: remixType, limit, offset },
    });
    return res.data;
  },

  getDashboard: async (topVideosLimit = 5) => {
    const res = await client.get<CreatorDashboard>('/api/videos/dashboard', {
      params: { top_videos_limit: topVideosLimit },
    });
    return res.data;
  },
};

export interface TopVideoSummary {
  video_id: string;
  title: string | null;
  thumbnail_url: string | null;
  views: number;
  likes: number;
  comments: number;
  engagement_rate: number;
  published_at: string | null;
}

export interface CreatorDashboard {
  video_count: number;
  total_views: number;
  total_likes: number;
  total_comments: number;
  total_shares: number;
  total_bookmarks: number;
  average_engagement_rate: number;
  followers_count: number;
  top_videos: TopVideoSummary[];
}

// Comment endpoints
export interface CommentListResult {
  comments: Comment[];
  total: number;
  limit: number;
  offset: number;
}

export const commentApi = {
  getComments: async (videoId: string, limit = 20, offset = 0) => {
    const res = await client.get<CommentListResult>(`/api/videos/${videoId}/comments`, {
      params: { limit, offset },
    });
    return res.data;
  },

  getReplies: async (commentId: string, limit = 20, offset = 0) => {
    const res = await client.get<CommentListResult>(`/api/comments/${commentId}/replies`, {
      params: { limit, offset },
    });
    return res.data;
  },

  createComment: async (videoId: string, content: string, parentCommentId?: string) => {
    const res = await client.post<Comment>(`/api/videos/${videoId}/comments`, {
      content,
      parent_comment_id: parentCommentId,
    });
    return res.data;
  },

  updateComment: async (id: string, content: string) => {
    const res = await client.put<Comment>(`/api/comments/${id}`, { content });
    return res.data;
  },

  deleteComment: async (id: string) => {
    await client.delete(`/api/comments/${id}`);
  },

  likeComment: async (id: string) => {
    const res = await client.post<{ is_liked: boolean; likes_count: number }>(
      `/api/comments/${id}/like`
    );
    return res.data;
  },

  pinComment: async (id: string) => {
    const res = await client.post<Comment>(`/api/comments/${id}/pin`);
    return res.data;
  },
};

// Note: there is no /api/users/* router on the backend - use profileApi for
// profile CRUD/follow/block and videoApi.getUserVideos for a user's videos.

// Notification endpoints
export interface NotificationItem {
  id: string;
  user_id: string;
  type: string;
  actor_id: string | null;
  related_video_id: string | null;
  related_comment_id: string | null;
  title: string;
  message: string | null;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
}

export interface NotificationListResult {
  notifications: NotificationItem[];
  total: number;
  unread_count: number;
  limit: number;
  offset: number;
}

export interface NotificationPreferences {
  id: string;
  push_enabled: boolean;
  email_enabled: boolean;
  in_app_enabled: boolean;
  follow_notifications: boolean;
  like_notifications: boolean;
  comment_notifications: boolean;
  mention_notifications: boolean;
  message_notifications: boolean;
  email_digest_enabled: boolean;
  email_digest_frequency: string;
  quiet_hours_enabled: boolean;
  quiet_hours_start: string | null;
  quiet_hours_end: string | null;
}

export const notificationApi = {
  getNotifications: async (limit = 20, offset = 0, unreadOnly = false) => {
    const res = await client.get<NotificationListResult>('/api/notifications', {
      params: { limit, offset, unread_only: unreadOnly },
    });
    return res.data;
  },

  markAsRead: async (id: string) => {
    const res = await client.put<NotificationItem>(`/api/notifications/${id}/read`);
    return res.data;
  },

  markAllAsRead: async () => {
    const res = await client.put<{ message: string; count: number }>('/api/notifications/read-all');
    return res.data;
  },

  deleteNotification: async (id: string) => {
    await client.delete(`/api/notifications/${id}`);
  },

  getPreferences: async () => {
    const res = await client.get<NotificationPreferences>('/api/notifications/preferences');
    return res.data;
  },

  updatePreferences: async (data: Partial<Omit<NotificationPreferences, 'id'>>) => {
    const res = await client.put<NotificationPreferences>('/api/notifications/preferences', data);
    return res.data;
  },
};

// Message endpoints
export interface ConversationListResult {
  conversations: Conversation[];
  total: number;
}

export interface MessageListResult {
  messages: Message[];
  total: number;
  limit: number;
  offset: number;
}

export const messageApi = {
  getConversations: async (limit = 20, offset = 0) => {
    const res = await client.get<ConversationListResult>('/api/messages/conversations', {
      params: { limit, offset },
    });
    return res.data;
  },

  startConversation: async (recipientId: string) => {
    const res = await client.post<Conversation>('/api/messages/conversations', null, {
      params: { recipient_id: recipientId },
    });
    return res.data;
  },

  getMessages: async (conversationId: string, limit = 30, offset = 0) => {
    const res = await client.get<MessageListResult>(
      `/api/messages/conversations/${conversationId}/messages`,
      { params: { limit, offset } }
    );
    return res.data;
  },

  sendMessage: async (conversationId: string, content: string) => {
    const res = await client.post<Message>(
      `/api/messages/conversations/${conversationId}/messages`,
      { content }
    );
    return res.data;
  },

  markRead: async (conversationId: string) => {
    const res = await client.put<{ count: number }>(
      `/api/messages/conversations/${conversationId}/read`
    );
    return res.data;
  },
};

// Search endpoints
// Search endpoints - the backend exposes separate endpoints per result type
// (there is no unified /api/search?q=...&type=... route), and all of them
// require authentication.
export const searchApi = {
  searchVideos: async (query: string, limit = 20, offset = 0) => {
    const res = await client.get('/api/search/videos', { params: { q: query, limit, offset } });
    return res.data as { results: Video[]; total: number };
  },

  searchCreators: async (query: string, limit = 20, offset = 0) => {
    const res = await client.get('/api/search/creators', { params: { q: query, limit, offset } });
    return res.data as { results: PublicUser[]; total: number };
  },

  searchHashtags: async (query: string, limit = 20) => {
    const res = await client.get('/api/search/hashtags', { params: { q: query, limit } });
    return res.data;
  },

  getSuggestions: async (query: string) => {
    const res = await client.get('/api/search/suggestions', { params: { q: query } });
    return res.data;
  },

  discoverByCategory: async (category: string, limit = 30) => {
    const res = await client.get(`/api/search/discover/${category}`, { params: { limit } });
    return res.data as { category: string; results: Video[]; total: number };
  },
};

export interface UserPreferences {
  id: string;
  preferred_creators: string[];
  preferred_hashtags: string[];
  preferred_genres: string[];
  preferred_languages: string[];
  avg_watch_time: number | null;
  content_diversity_score: number;
  recency_preference: number;
  updated_at: string;
}

export interface Recommendation {
  id: string;
  video_id: string;
  score: number;
  algorithm: string;
  reason: string | null;
  video: Video;
  created_at: string;
}

export interface RecommendationsListResponse {
  recommendations: Recommendation[];
  cursor: string | null;
  total: number;
}

// Recommendation endpoints (Module 7)
export const recommendationApi = {
  getPreferences: async () => {
    const res = await client.get<UserPreferences>('/api/recommendations/preferences');
    return res.data;
  },

  updatePreferences: async (data: {
    preferred_hashtags?: string[];
    preferred_genres?: string[];
    preferred_languages?: string[];
    content_diversity_score?: number;
    recency_preference?: number;
  }) => {
    const res = await client.put<UserPreferences>('/api/recommendations/preferences', data);
    return res.data;
  },

  getForYouFeed: async (limit = 30, cursor?: string) => {
    const res = await client.get<RecommendationsListResponse>('/api/recommendations/for-you', {
      params: { limit, cursor },
    });
    return res.data;
  },

  getSimilarVideos: async (videoId: string, limit = 10) => {
    const res = await client.get<FeedResponse>(`/api/recommendations/similar/${videoId}`, {
      params: { limit },
    });
    return res.data;
  },

  recordFeedback: async (
    recommendationId: string,
    feedbackType: 'relevant' | 'irrelevant' | 'duplicate' | 'nsfw' | 'not_interested',
    reason?: string
  ) => {
    await client.post(`/api/recommendations/${recommendationId}/feedback`, {
      feedback_type: feedbackType,
      reason,
    });
  },
};

export interface HashtagTrend {
  id: string;
  hashtag: string;
  region: string;
  usage_count: number;
  unique_creators: number;
  total_views: number;
  popularity_score: number;
  trend_velocity: number;
  rank_position: number | null;
  category: string | null;
  is_challenge: boolean;
}

export interface Challenge {
  id: string;
  hashtag: string;
  title: string;
  description: string | null;
  thumbnail_url: string | null;
  start_date: string;
  end_date: string;
  prize_pool: number | null;
  participation_count: number;
  is_active: boolean;
}

// Hashtag trending & challenges endpoints (Module 9)
export const hashtagApi = {
  getTrending: async (region = 'US', limit = 20) => {
    const res = await client.get<HashtagTrend[]>('/api/hashtags/trending', {
      params: { region, limit },
    });
    return res.data;
  },

  getStats: async (hashtag: string, region = 'US') => {
    const res = await client.get(`/api/hashtags/${encodeURIComponent(hashtag)}/stats`, {
      params: { region },
    });
    return res.data;
  },

  search: async (query: string, region = 'US', limit = 20) => {
    const res = await client.get<HashtagTrend[]>('/api/hashtags/search', {
      params: { q: query, region, limit },
    });
    return res.data;
  },

  getActiveChallenges: async (region = 'US', limit = 10) => {
    const res = await client.get<Challenge[]>('/api/hashtags/challenges/active', {
      params: { region, limit },
    });
    return res.data;
  },

  getChallengeVideos: async (challengeId: string, limit = 30, offset = 0) => {
    const res = await client.get(`/api/hashtags/challenges/${challengeId}/videos`, {
      params: { limit, offset },
    });
    return res.data as { videos: Video[]; total: number; limit: number; offset: number };
  },

  getChallengeDetails: async (challengeId: string) => {
    const res = await client.get<Challenge>(`/api/hashtags/challenges/${challengeId}`);
    return res.data;
  },

  getAnalytics: async (hashtag: string, days = 30) => {
    const res = await client.get<HashtagAnalytics[]>(
      `/api/hashtags/${encodeURIComponent(hashtag)}/analytics`,
      { params: { days } }
    );
    return res.data;
  },
};

export interface HashtagAnalytics {
  id: string;
  hashtag: string;
  date: string;
  usage_count: number;
  unique_creators: number;
  total_views: number;
  total_engagement: number;
}

export type ReportedContentType = 'video' | 'comment' | 'user';
export type ReportReason =
  | 'spam'
  | 'harassment'
  | 'nudity'
  | 'violence'
  | 'hate_speech'
  | 'misinformation'
  | 'self_harm'
  | 'other';
export type ReportStatus = 'pending' | 'actioned' | 'dismissed';
export type ModerationActionType = 'dismiss' | 'remove_content' | 'warn_user' | 'suspend_user' | 'ban_user';

export interface ContentReport {
  id: string;
  reporter_id: string;
  content_type: ReportedContentType;
  reported_video_id: string | null;
  reported_comment_id: string | null;
  reported_user_id: string | null;
  reason: ReportReason;
  description: string | null;
  status: ReportStatus;
  created_at: string;
}

export interface ContentReportListResult {
  reports: ContentReport[];
  total: number;
  limit: number;
  offset: number;
}

export const moderationApi = {
  createReport: async (data: {
    content_type: ReportedContentType;
    content_id: string;
    reason: ReportReason;
    description?: string;
  }) => {
    const res = await client.post<ContentReport>('/api/moderation/reports', data);
    return res.data;
  },

  getMyReports: async (limit = 20, offset = 0) => {
    const res = await client.get<ContentReportListResult>('/api/moderation/reports/me', {
      params: { limit, offset },
    });
    return res.data;
  },

  getReportQueue: async (params?: { status?: ReportStatus; content_type?: ReportedContentType; limit?: number; offset?: number }) => {
    const res = await client.get<ContentReportListResult>('/api/moderation/reports', { params });
    return res.data;
  },

  decideReport: async (reportId: string, action: ModerationActionType, notes?: string) => {
    const res = await client.post(`/api/moderation/reports/${reportId}/decide`, { action, notes });
    return res.data;
  },
};

export interface AdminStats {
  total_users: number;
  active_users: number;
  suspended_users: number;
  total_videos: number;
  total_comments: number;
  pending_reports: number;
  actioned_reports: number;
  dismissed_reports: number;
}

export interface AdminUserSummary {
  id: string;
  email: string;
  username: string;
  avatar_url: string | null;
  is_active: boolean;
  is_verified: boolean;
  is_creator: boolean;
  role: 'user' | 'creator' | 'admin';
  created_at: string;
  last_login: string | null;
}

export interface AdminUserListResult {
  users: AdminUserSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface AdminAuditLogEntry {
  id: string;
  report_id: string;
  moderator_id: string;
  moderator_username: string;
  action: ModerationActionType;
  notes: string | null;
  report_content_type: ReportedContentType;
  report_reason: ReportReason;
  created_at: string;
}

export interface AdminAuditLogResult {
  entries: AdminAuditLogEntry[];
  total: number;
  limit: number;
  offset: number;
}

export interface FundingProgram {
  id: string;
  name: string;
  description: string | null;
  min_followers: number;
  min_published_videos: number;
  min_total_views: number;
  award_amount: number;
  is_active: boolean;
  created_at: string;
}

export interface CreatorApplication {
  id: string;
  program_id: string;
  user_id: string;
  followers_count: number;
  published_videos_count: number;
  total_views_count: number;
  meets_requirements: boolean;
  status: 'pending' | 'approved' | 'rejected';
  decision_reason: string | null;
  awarded_amount: number | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
  created_at: string;
}

export interface CreatorApplicationListResult {
  applications: CreatorApplication[];
  total: number;
  limit: number;
  offset: number;
}

export const creatorFundApi = {
  listPrograms: async () => {
    const res = await client.get<{ programs: FundingProgram[] }>('/api/creator-fund/programs');
    return res.data.programs;
  },

  applyToProgram: async (programId: string) => {
    const res = await client.post<CreatorApplication>(`/api/creator-fund/programs/${programId}/apply`);
    return res.data;
  },

  getMyApplications: async () => {
    const res = await client.get<CreatorApplication[]>('/api/creator-fund/me/applications');
    return res.data;
  },

  createProgram: async (data: {
    name: string;
    description?: string;
    min_followers: number;
    min_published_videos: number;
    min_total_views: number;
    award_amount: number;
  }) => {
    const res = await client.post<FundingProgram>('/api/creator-fund/programs', data);
    return res.data;
  },

  listApplications: async (status?: string, limit = 20, offset = 0) => {
    const res = await client.get<CreatorApplicationListResult>('/api/creator-fund/admin/applications', {
      params: { status, limit, offset },
    });
    return res.data;
  },

  decideApplication: async (applicationId: string, status: 'approved' | 'rejected', decisionReason?: string) => {
    const res = await client.post<CreatorApplication>(
      `/api/creator-fund/admin/applications/${applicationId}/decide`,
      { status, decision_reason: decisionReason }
    );
    return res.data;
  },
};

export interface CollaboratorSplit {
  id: string;
  user_id: string;
  revenue_split_percent: number;
  is_initiator: boolean;
  status: 'invited' | 'accepted' | 'declined';
  responded_at: string | null;
}

export interface Collaboration {
  id: string;
  video_id: string;
  initiator_id: string;
  title: string | null;
  status: 'pending' | 'active' | 'cancelled';
  collaborators: CollaboratorSplit[];
  created_at: string;
}

export const collaborationsApi = {
  create: async (data: {
    video_id: string;
    title?: string;
    collaborators: { user_id: string; revenue_split_percent: number }[];
  }) => {
    const res = await client.post<Collaboration>('/api/collaborations', data);
    return res.data;
  },

  listMine: async () => {
    const res = await client.get<Collaboration[]>('/api/collaborations/me');
    return res.data;
  },

  get: async (collaborationId: string) => {
    const res = await client.get<Collaboration>(`/api/collaborations/${collaborationId}`);
    return res.data;
  },

  respond: async (collaborationId: string, accept: boolean) => {
    const res = await client.post<Collaboration>(`/api/collaborations/${collaborationId}/respond`, { accept });
    return res.data;
  },

  cancel: async (collaborationId: string) => {
    const res = await client.post<Collaboration>(`/api/collaborations/${collaborationId}/cancel`);
    return res.data;
  },
};

export interface Shop {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
}

export interface ShopProduct {
  id: string;
  shop_id: string;
  name: string;
  description: string | null;
  price: number;
  image_url: string | null;
  stock_quantity: number | null;
  is_active: boolean;
  created_at: string;
}

export interface ShopOrder {
  id: string;
  product_id: string;
  shop_id: string;
  buyer_id: string;
  quantity: number;
  total_amount: number;
  status: 'pending' | 'fulfilled' | 'cancelled';
  created_at: string;
  fulfilled_at: string | null;
  cancelled_at: string | null;
}

export const shopApi = {
  upsertMyShop: async (name: string, description?: string) => {
    const res = await client.post<Shop>('/api/shop/me', { name, description });
    return res.data;
  },

  getMyShop: async () => {
    const res = await client.get<Shop>('/api/shop/me');
    return res.data;
  },

  getShop: async (shopId: string) => {
    const res = await client.get<{ shop: Shop; products: ShopProduct[] }>(`/api/shop/${shopId}`);
    return res.data;
  },

  getShopByUser: async (userId: string) => {
    const res = await client.get<{ shop: Shop; products: ShopProduct[] }>(`/api/shop/user/${userId}`);
    return res.data;
  },

  createProduct: async (data: {
    name: string;
    description?: string;
    price: number;
    image_url?: string;
    stock_quantity?: number | null;
  }) => {
    const res = await client.post<ShopProduct>('/api/shop/products', data);
    return res.data;
  },

  updateProduct: async (productId: string, data: Partial<{
    name: string;
    description: string;
    price: number;
    image_url: string;
    stock_quantity: number | null;
    is_active: boolean;
  }>) => {
    const res = await client.put<ShopProduct>(`/api/shop/products/${productId}`, data);
    return res.data;
  },

  deleteProduct: async (productId: string) => {
    await client.delete(`/api/shop/products/${productId}`);
  },

  orderProduct: async (productId: string, quantity = 1) => {
    const res = await client.post<ShopOrder>(`/api/shop/products/${productId}/order`, { quantity });
    return res.data;
  },

  getMyOrders: async () => {
    const res = await client.get<{ orders: ShopOrder[] }>('/api/shop/orders/me');
    return res.data.orders;
  },

  getReceivedOrders: async () => {
    const res = await client.get<{ orders: ShopOrder[] }>('/api/shop/orders/received');
    return res.data.orders;
  },

  fulfillOrder: async (orderId: string) => {
    const res = await client.post<ShopOrder>(`/api/shop/orders/${orderId}/fulfill`);
    return res.data;
  },

  cancelOrder: async (orderId: string) => {
    const res = await client.post<ShopOrder>(`/api/shop/orders/${orderId}/cancel`);
    return res.data;
  },
};

export interface Earning {
  id: string;
  source_type: 'creator_fund' | 'shop_order';
  fund_application_id: string | null;
  shop_order_id: string | null;
  amount: number;
  created_at: string;
}

export interface EarningsSummary {
  total_earned: number;
  total_paid_out: number;
  pending_payout_total: number;
  available_balance: number;
  earnings: Earning[];
}

export interface Payout {
  id: string;
  user_id: string;
  amount: number;
  status: 'pending' | 'completed' | 'cancelled';
  notes: string | null;
  requested_at: string;
  decided_at: string | null;
}

export interface PayoutListResult {
  payouts: Payout[];
  total: number;
  limit: number;
  offset: number;
}

export const monetizationApi = {
  getSummary: async () => {
    const res = await client.get<EarningsSummary>('/api/monetization/summary');
    return res.data;
  },

  requestPayout: async (amount: number) => {
    const res = await client.post<Payout>('/api/monetization/payouts', { amount });
    return res.data;
  },

  getMyPayouts: async () => {
    const res = await client.get<Payout[]>('/api/monetization/payouts/me');
    return res.data;
  },

  listPayouts: async (status?: string, limit = 20, offset = 0) => {
    const res = await client.get<PayoutListResult>('/api/monetization/admin/payouts', {
      params: { status, limit, offset },
    });
    return res.data;
  },

  decidePayout: async (payoutId: string, status: 'completed' | 'cancelled', notes?: string) => {
    const res = await client.post<Payout>(`/api/monetization/admin/payouts/${payoutId}/decide`, { status, notes });
    return res.data;
  },
};

export interface LiveStream {
  id: string;
  creator_id: string;
  title: string;
  status: 'live' | 'ended';
  viewer_count: number;
  peak_viewer_count: number;
  started_at: string;
  ended_at: string | null;
}

export interface LiveChatMessage {
  id: string;
  stream_id: string;
  user_id: string;
  username: string;
  content: string;
  created_at: string;
}

export const liveApi = {
  startStream: async (title: string) => {
    const res = await client.post<LiveStream>('/api/live/start', { title });
    return res.data;
  },

  listLiveStreams: async () => {
    const res = await client.get<{ streams: LiveStream[] }>('/api/live');
    return res.data.streams;
  },

  getStream: async (streamId: string) => {
    const res = await client.get<LiveStream>(`/api/live/${streamId}`);
    return res.data;
  },

  endStream: async (streamId: string) => {
    const res = await client.post<LiveStream>(`/api/live/${streamId}/end`);
    return res.data;
  },

  joinStream: async (streamId: string) => {
    const res = await client.post<LiveStream>(`/api/live/${streamId}/join`);
    return res.data;
  },

  leaveStream: async (streamId: string) => {
    const res = await client.post<LiveStream>(`/api/live/${streamId}/leave`);
    return res.data;
  },

  postChatMessage: async (streamId: string, content: string) => {
    const res = await client.post<LiveChatMessage>(`/api/live/${streamId}/chat`, { content });
    return res.data;
  },

  getChatMessages: async (streamId: string) => {
    const res = await client.get<{ messages: LiveChatMessage[] }>(`/api/live/${streamId}/chat`);
    return res.data.messages;
  },
};

export const adminApi = {
  getStats: async () => {
    const res = await client.get<AdminStats>('/api/admin/stats');
    return res.data;
  },

  getUsers: async (search?: string, limit = 20, offset = 0) => {
    const res = await client.get<AdminUserListResult>('/api/admin/users', {
      params: { search, limit, offset },
    });
    return res.data;
  },

  suspendUser: async (userId: string) => {
    const res = await client.post<AdminUserSummary>(`/api/admin/users/${userId}/suspend`);
    return res.data;
  },

  reactivateUser: async (userId: string) => {
    const res = await client.post<AdminUserSummary>(`/api/admin/users/${userId}/reactivate`);
    return res.data;
  },

  getAuditLog: async (limit = 20, offset = 0) => {
    const res = await client.get<AdminAuditLogResult>('/api/admin/audit-log', {
      params: { limit, offset },
    });
    return res.data;
  },
};

export default client;
