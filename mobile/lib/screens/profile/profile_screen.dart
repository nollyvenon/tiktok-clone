import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/profile.dart';
import '../../providers/auth_provider.dart';
import '../../services/profile_service.dart';
import '../settings/preferences_screen.dart';
import '../bookmarks/bookmarks_screen.dart';
import '../dashboard/dashboard_screen.dart';
import '../messages/messages_screen.dart';
import '../messages/chat_detail_screen.dart';
import '../../services/message_service.dart';
import 'edit_profile_screen.dart';
import 'follow_list_screen.dart';

class ProfileScreen extends StatefulWidget {
  final String? userId;

  const ProfileScreen({super.key, this.userId});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _profileService = ProfileService();
  final _messageService = MessageService();
  ProfileDetail? _profile;
  bool _isLoading = true;
  bool _isFollowActionPending = false;
  bool _isMessageActionPending = false;
  String? _error;

  bool get _isOwnProfile {
    final authUser = context.read<AuthProvider>().user;
    return widget.userId == null || widget.userId == authUser?.id;
  }

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final authUser = context.read<AuthProvider>().user;
      final targetId = widget.userId ?? authUser?.id;
      if (targetId == null) throw Exception('No user to load');
      final profile = await _profileService.getProfile(targetId);
      setState(() => _profile = profile);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _startConversation() async {
    if (_profile == null) return;
    setState(() => _isMessageActionPending = true);
    try {
      final conversation = await _messageService.startConversation(_profile!.user.id);
      if (!mounted) return;
      await Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => ChatDetailScreen(
            conversationId: conversation.id,
            otherUsername: conversation.otherUser.username,
          ),
        ),
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
      }
    } finally {
      if (mounted) setState(() => _isMessageActionPending = false);
    }
  }

  Future<void> _toggleBlock() async {
    if (_profile == null) return;
    try {
      final isBlocked = await _profileService.toggleBlock(_profile!.user.id);
      setState(() {
        _profile = ProfileDetail(
          user: _profile!.user,
          statistics: _profile!.statistics,
          isFollowing: isBlocked ? false : _profile!.isFollowing,
          isBlocked: isBlocked,
        );
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
      }
    }
  }

  Future<void> _toggleFollow() async {
    if (_profile == null) return;
    setState(() => _isFollowActionPending = true);
    try {
      final isFollowing = await _profileService.toggleFollow(_profile!.user.id);
      setState(() {
        _profile = ProfileDetail(
          user: _profile!.user,
          statistics: ProfileStatistics(
            followersCount: _profile!.statistics.followersCount + (isFollowing ? 1 : -1),
            followingCount: _profile!.statistics.followingCount,
            videosCount: _profile!.statistics.videosCount,
            likesCount: _profile!.statistics.likesCount,
            totalViews: _profile!.statistics.totalViews,
          ),
          isFollowing: isFollowing,
          isBlocked: _profile!.isBlocked,
        );
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
      }
    } finally {
      setState(() => _isFollowActionPending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_profile?.user.username ?? 'Profile'),
        actions: [
          if (_isOwnProfile) ...[
            IconButton(
              icon: const Icon(Icons.chat_bubble_outline),
              tooltip: 'Messages',
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const MessagesScreen()),
              ),
            ),
            IconButton(
              icon: const Icon(Icons.bookmark_border),
              tooltip: 'Saved Videos',
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const BookmarksScreen()),
              ),
            ),
            IconButton(
              icon: const Icon(Icons.bar_chart),
              tooltip: 'Creator Dashboard',
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const DashboardScreen()),
              ),
            ),
            IconButton(
              icon: const Icon(Icons.tune),
              tooltip: 'For You Preferences',
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const PreferencesScreen()),
              ),
            ),
            IconButton(
              icon: const Icon(Icons.logout),
              onPressed: () => context.read<AuthProvider>().logout(),
            ),
          ] else if (_profile != null)
            PopupMenuButton<String>(
              onSelected: (value) {
                if (value == 'block') _toggleBlock();
              },
              itemBuilder: (context) => [
                PopupMenuItem(
                  value: 'block',
                  child: Text(_profile!.isBlocked ? 'Unblock' : 'Block'),
                ),
              ],
            ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : RefreshIndicator(
                  onRefresh: _loadProfile,
                  child: _buildProfileContent(),
                ),
    );
  }

  Widget _buildProfileContent() {
    final profile = _profile!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        CircleAvatar(
          radius: 48,
          backgroundImage:
              profile.user.avatarUrl != null ? NetworkImage(profile.user.avatarUrl!) : null,
          child: profile.user.avatarUrl == null ? const Icon(Icons.person, size: 48) : null,
        ),
        const SizedBox(height: 12),
        Center(
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                '@${profile.user.username}',
                style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
              if (profile.user.isVerified) ...[
                const SizedBox(width: 4),
                const Icon(Icons.verified, color: Colors.blue, size: 20),
              ],
            ],
          ),
        ),
        if (profile.user.bio != null && profile.user.bio!.isNotEmpty) ...[
          const SizedBox(height: 8),
          Text(profile.user.bio!, textAlign: TextAlign.center),
        ],
        const SizedBox(height: 20),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            _StatColumn(label: 'Videos', count: profile.statistics.videosCount),
            _StatColumn(
              label: 'Followers',
              count: profile.statistics.followersCount,
              onTap: () => Navigator.of(context).push(MaterialPageRoute(
                builder: (_) => FollowListScreen(userId: profile.user.id, mode: FollowListMode.followers),
              )),
            ),
            _StatColumn(
              label: 'Following',
              count: profile.statistics.followingCount,
              onTap: () => Navigator.of(context).push(MaterialPageRoute(
                builder: (_) => FollowListScreen(userId: profile.user.id, mode: FollowListMode.following),
              )),
            ),
            _StatColumn(label: 'Likes', count: profile.statistics.likesCount),
          ],
        ),
        const SizedBox(height: 20),
        if (_isOwnProfile)
          SizedBox(
            height: 44,
            child: OutlinedButton(
              onPressed: () async {
                await Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => EditProfileScreen(user: profile.user)),
                );
                _loadProfile();
              },
              child: const Text('Edit profile'),
            ),
          )
        else
          Row(
            children: [
              Expanded(
                child: SizedBox(
                  height: 44,
                  child: ElevatedButton(
                    onPressed: _isFollowActionPending || profile.isBlocked ? null : _toggleFollow,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: profile.isFollowing ? Colors.grey.shade300 : Colors.pink,
                      foregroundColor: profile.isFollowing ? Colors.black : Colors.white,
                    ),
                    child: Text(profile.isFollowing ? 'Following' : 'Follow'),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              SizedBox(
                height: 44,
                width: 44,
                child: OutlinedButton(
                  onPressed: _isMessageActionPending || profile.isBlocked ? null : _startConversation,
                  style: OutlinedButton.styleFrom(padding: EdgeInsets.zero),
                  child: const Icon(Icons.chat_bubble_outline, size: 18),
                ),
              ),
            ],
          ),
        if (profile.isBlocked && !_isOwnProfile)
          const Padding(
            padding: EdgeInsets.only(top: 8),
            child: Text('You have blocked this user.', style: TextStyle(color: Colors.red, fontSize: 12)),
          ),
      ],
    );
  }
}

class _StatColumn extends StatelessWidget {
  final String label;
  final int count;
  final VoidCallback? onTap;

  const _StatColumn({required this.label, required this.count, this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          Text('$count', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          Text(label, style: TextStyle(color: Colors.grey.shade600)),
        ],
      ),
    );
  }
}
