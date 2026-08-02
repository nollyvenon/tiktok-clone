import 'package:flutter/material.dart';

import '../../models/video.dart';
import '../../services/feed_service.dart';
import '../../services/notification_service.dart';
import '../../widgets/video_player_item.dart';
import '../../widgets/comments_sheet.dart';
import '../notifications/notifications_screen.dart';
import '../profile/profile_screen.dart';
import '../upload/upload_screen.dart';

class FeedScreen extends StatefulWidget {
  const FeedScreen({super.key});

  @override
  State<FeedScreen> createState() => _FeedScreenState();
}

class _FeedScreenState extends State<FeedScreen> {
  final _feedService = FeedService();
  final _notificationService = NotificationService();
  final _pageController = PageController();
  final List<Video> _videos = [];
  int _activeIndex = 0;
  bool _isLoading = true;
  bool _isLoadingMore = false;
  String? _error;
  int _unreadNotifications = 0;

  @override
  void initState() {
    super.initState();
    _loadFeed();
    _loadUnreadCount();
  }

  Future<void> _loadUnreadCount() async {
    try {
      final page = await _notificationService.getNotifications(limit: 1, unreadOnly: true);
      if (mounted) setState(() => _unreadNotifications = page.unreadCount);
    } catch (_) {
      // Non-critical: badge just stays at 0 if this fails
    }
  }

  Future<void> _loadFeed() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final page = await _feedService.getFeed();
      setState(() => _videos.addAll(page.videos));
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _loadMore() async {
    if (_isLoadingMore) return;
    setState(() => _isLoadingMore = true);
    try {
      final page = await _feedService.getFeed(offset: _videos.length);
      setState(() => _videos.addAll(page.videos));
    } catch (_) {
      // Silently ignore pagination failures; user can pull-to-refresh
    } finally {
      setState(() => _isLoadingMore = false);
    }
  }

  Future<void> _toggleLike(int index) async {
    final video = _videos[index];
    final wasLiked = video.isLiked;
    setState(() {
      video.isLiked = !wasLiked;
      video.likesCount += wasLiked ? -1 : 1;
    });
    try {
      final isLiked = await _feedService.toggleLike(video.id);
      setState(() => video.isLiked = isLiked);
    } catch (_) {
      setState(() {
        video.isLiked = wasLiked;
        video.likesCount += wasLiked ? 1 : -1;
      });
    }
  }

  Future<void> _toggleBookmark(int index) async {
    final video = _videos[index];
    final wasBookmarked = video.isBookmarked;
    setState(() {
      video.isBookmarked = !wasBookmarked;
      video.bookmarksCount += wasBookmarked ? -1 : 1;
    });
    try {
      final isBookmarked = await _feedService.toggleBookmark(video.id);
      setState(() => video.isBookmarked = isBookmarked);
    } catch (_) {
      setState(() {
        video.isBookmarked = wasBookmarked;
        video.bookmarksCount += wasBookmarked ? 1 : -1;
      });
    }
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        backgroundColor: Colors.black,
        body: Center(child: CircularProgressIndicator(color: Colors.white)),
      );
    }

    if (_error != null) {
      return Scaffold(
        backgroundColor: Colors.black,
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(_error!, style: const TextStyle(color: Colors.white)),
              const SizedBox(height: 12),
              ElevatedButton(onPressed: _loadFeed, child: const Text('Retry')),
            ],
          ),
        ),
      );
    }

    if (_videos.isEmpty) {
      return const Scaffold(
        backgroundColor: Colors.black,
        body: Center(child: Text('No videos yet', style: TextStyle(color: Colors.white))),
      );
    }

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          PageView.builder(
            controller: _pageController,
            scrollDirection: Axis.vertical,
            itemCount: _videos.length,
            onPageChanged: (index) {
              setState(() => _activeIndex = index);
              if (index >= _videos.length - 3) _loadMore();
            },
            itemBuilder: (context, index) {
              final video = _videos[index];
              return Stack(
                fit: StackFit.expand,
                children: [
                  VideoPlayerItem(video: video, isActive: index == _activeIndex),
                  Positioned(
                    left: 12,
                    right: 80,
                    bottom: 24,
                    child: _VideoInfo(video: video),
                  ),
                  Positioned(
                    right: 12,
                    bottom: 24,
                    child: _EngagementBar(
                      video: video,
                      onLike: () => _toggleLike(index),
                      onBookmark: () => _toggleBookmark(index),
                      onComment: () => CommentsSheet.show(
                        context,
                        videoId: video.id,
                        videoOwnerId: video.author.id,
                        onCommentCountChanged: (delta) {
                          setState(() => video.commentsCount += delta);
                        },
                      ),
                      onDuet: () => Navigator.of(context).push(MaterialPageRoute(
                        builder: (_) => UploadScreen(
                          originalVideoId: video.id,
                          originalVideoUsername: video.author.username,
                          remixType: 'duet',
                        ),
                      )),
                      onStitch: () => Navigator.of(context).push(MaterialPageRoute(
                        builder: (_) => UploadScreen(
                          originalVideoId: video.id,
                          originalVideoUsername: video.author.username,
                          remixType: 'stitch',
                        ),
                      )),
                    ),
                  ),
                ],
              );
            },
          ),
          Positioned(
            top: 8,
            right: 8,
            child: SafeArea(
              child: IconButton(
                icon: Badge(
                  isLabelVisible: _unreadNotifications > 0,
                  label: Text('$_unreadNotifications'),
                  child: const Icon(Icons.notifications, color: Colors.white),
                ),
                onPressed: () async {
                  await Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const NotificationsScreen()),
                  );
                  _loadUnreadCount();
                },
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _VideoInfo extends StatelessWidget {
  final Video video;

  const _VideoInfo({required this.video});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => ProfileScreen(userId: video.author.id)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              Text(
                '@${video.author.username}',
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
              ),
              if (video.author.isVerified) ...[
                const SizedBox(width: 4),
                const Icon(Icons.verified, color: Colors.lightBlueAccent, size: 16),
              ],
            ],
          ),
          if (video.originalVideo != null) ...[
            const SizedBox(height: 4),
            Row(
              children: [
                Icon(
                  video.remixType == 'duet' ? Icons.repeat : Icons.content_cut,
                  color: Colors.white70,
                  size: 14,
                ),
                const SizedBox(width: 4),
                Text(
                  '${video.remixType == 'duet' ? 'Duet with' : 'Stitch of'} @${video.originalVideo!.user.username}',
                  style: const TextStyle(color: Colors.white70, fontSize: 13),
                ),
              ],
            ),
          ],
          if (video.title != null && video.title!.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(video.title!, style: const TextStyle(color: Colors.white)),
          ],
          if (video.hashtagList.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(
              video.hashtagList.map((t) => '#$t').join(' '),
              style: const TextStyle(color: Colors.white70, fontSize: 13),
            ),
          ],
        ],
      ),
    );
  }
}

class _EngagementBar extends StatelessWidget {
  final Video video;
  final VoidCallback onLike;
  final VoidCallback onBookmark;
  final VoidCallback onComment;
  final VoidCallback onDuet;
  final VoidCallback onStitch;

  const _EngagementBar({
    required this.video,
    required this.onLike,
    required this.onBookmark,
    required this.onComment,
    required this.onDuet,
    required this.onStitch,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        CircleAvatar(
          radius: 22,
          backgroundImage: video.author.avatarUrl != null ? NetworkImage(video.author.avatarUrl!) : null,
          child: video.author.avatarUrl == null ? const Icon(Icons.person) : null,
        ),
        const SizedBox(height: 20),
        _ActionIcon(
          icon: video.isLiked ? Icons.favorite : Icons.favorite_border,
          color: video.isLiked ? Colors.red : Colors.white,
          label: '${video.likesCount}',
          onTap: onLike,
        ),
        const SizedBox(height: 20),
        _ActionIcon(
          icon: Icons.comment,
          color: Colors.white,
          label: '${video.commentsCount}',
          onTap: onComment,
        ),
        const SizedBox(height: 20),
        _ActionIcon(
          icon: video.isBookmarked ? Icons.bookmark : Icons.bookmark_border,
          color: video.isBookmarked ? Colors.amber : Colors.white,
          label: '${video.bookmarksCount}',
          onTap: onBookmark,
        ),
        const SizedBox(height: 20),
        _ActionIcon(icon: Icons.share, color: Colors.white, label: '${video.sharesCount}', onTap: () {}),
        if (video.allowDuets) ...[
          const SizedBox(height: 20),
          _ActionIcon(icon: Icons.repeat, color: Colors.white, label: 'Duet', onTap: onDuet),
        ],
        if (video.allowStitches) ...[
          const SizedBox(height: 20),
          _ActionIcon(icon: Icons.content_cut, color: Colors.white, label: 'Stitch', onTap: onStitch),
        ],
      ],
    );
  }
}

class _ActionIcon extends StatelessWidget {
  final IconData icon;
  final Color color;
  final String label;
  final VoidCallback onTap;

  const _ActionIcon({required this.icon, required this.color, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          Icon(icon, color: color, size: 32),
          const SizedBox(height: 4),
          Text(label, style: const TextStyle(color: Colors.white, fontSize: 12)),
        ],
      ),
    );
  }
}
