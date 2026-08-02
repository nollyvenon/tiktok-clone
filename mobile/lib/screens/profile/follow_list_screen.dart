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
  final _searchController = TextEditingController();
  bool _isLoading = true;
  String? _error;
  String _query = '';

  @override
  void initState() {
    super.initState();
    _load();
    _searchController.addListener(() {
      setState(() => _query = _searchController.text);
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
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
    final filtered = _users
        .where((u) => u.username.toLowerCase().contains(_query.toLowerCase()))
        .toList();
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: Column(
        children: [
          if (!_isLoading && _error == null && _users.isNotEmpty)
            Padding(
              padding: const EdgeInsets.all(12),
              child: TextField(
                controller: _searchController,
                decoration: InputDecoration(
                  hintText: 'Search ${title.toLowerCase()}...',
                  prefixIcon: const Icon(Icons.search),
                  isDense: true,
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(24)),
                ),
              ),
            ),
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _error != null
                    ? Center(child: Text(_error!))
                    : filtered.isEmpty
                        ? Center(
                            child: Text(
                              _query.isNotEmpty ? 'No matches found' : 'No ${title.toLowerCase()} yet',
                            ),
                          )
                        : ListView.builder(
                            itemCount: filtered.length,
                            itemBuilder: (context, index) {
                              final user = filtered[index];
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
                                subtitle: user.isFollowedBy ? const Text('Follows you') : null,
                                trailing: user.isFollowing
                                    ? Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                        decoration: BoxDecoration(
                                          color: Colors.grey.shade200,
                                          borderRadius: BorderRadius.circular(12),
                                        ),
                                        child: const Text('Following', style: TextStyle(fontSize: 12)),
                                      )
                                    : null,
                                onTap: () => Navigator.of(context).push(
                                  MaterialPageRoute(builder: (_) => ProfileScreen(userId: user.id)),
                                ),
                              );
                            },
                          ),
          ),
        ],
      ),
    );
  }
}
