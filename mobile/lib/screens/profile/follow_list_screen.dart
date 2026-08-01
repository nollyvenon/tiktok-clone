import 'package:flutter/material.dart';

import '../../models/user.dart';
import '../../services/profile_service.dart';
import 'profile_screen.dart';

enum FollowListMode { followers, following }

class FollowListScreen extends StatefulWidget {
  final String userId;
  final FollowListMode mode;

  const FollowListScreen({super.key, required this.userId, required this.mode});

  @override
  State<FollowListScreen> createState() => _FollowListScreenState();
}

class _FollowListScreenState extends State<FollowListScreen> {
  final _profileService = ProfileService();
  final List<User> _users = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final users = widget.mode == FollowListMode.followers
          ? await _profileService.getFollowers(widget.userId)
          : await _profileService.getFollowing(widget.userId);
      setState(() {
        _users.addAll(users);
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final title = widget.mode == FollowListMode.followers ? 'Followers' : 'Following';
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : _users.isEmpty
                  ? Center(child: Text('No ${title.toLowerCase()} yet'))
                  : ListView.builder(
                      itemCount: _users.length,
                      itemBuilder: (context, index) {
                        final user = _users[index];
                        return ListTile(
                          leading: CircleAvatar(
                            backgroundImage:
                                user.avatarUrl != null ? NetworkImage(user.avatarUrl!) : null,
                            child: user.avatarUrl == null ? const Icon(Icons.person) : null,
                          ),
                          title: Row(
                            children: [
                              Text('@${user.username}'),
                              if (user.isVerified) ...[
                                const SizedBox(width: 4),
                                const Icon(Icons.verified, color: Colors.blue, size: 16),
                              ],
                            ],
                          ),
                          subtitle: user.firstName != null ? Text(user.displayName) : null,
                          onTap: () => Navigator.of(context).push(
                            MaterialPageRoute(builder: (_) => ProfileScreen(userId: user.id)),
                          ),
                        );
                      },
                    ),
    );
  }
}
