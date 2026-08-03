import 'package:flutter/material.dart';

import '../../models/user.dart';
import '../../services/profile_service.dart';
import '../../services/auth_service.dart';
import '../profile/profile_screen.dart';

class BlockedUsersScreen extends StatefulWidget {
  const BlockedUsersScreen({super.key});

  @override
  State<BlockedUsersScreen> createState() => _BlockedUsersScreenState();
}

class _BlockedUsersScreenState extends State<BlockedUsersScreen> {
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
    setState(() => _isLoading = true);
    try {
      final users = await _profileService.getBlockedUsers();
      if (!mounted) return;
      setState(() {
        _users
          ..clear()
          ..addAll(users);
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _unblock(User user) async {
    try {
      await _profileService.toggleBlock(user.id);
      if (!mounted) return;
      setState(() => _users.removeWhere((u) => u.id == user.id));
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Blocked Users')),
      body: RefreshIndicator(
        onRefresh: _load,
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
                ? Center(child: Text(_error!))
                : _users.isEmpty
                    ? ListView(
                        children: const [
                          Padding(
                            padding: EdgeInsets.only(top: 120),
                            child: Center(
                              child: Text("You haven't blocked anyone.", style: TextStyle(color: Colors.grey)),
                            ),
                          ),
                        ],
                      )
                    : ListView.builder(
                        itemCount: _users.length,
                        itemBuilder: (context, index) {
                          final user = _users[index];
                          return ListTile(
                            leading: CircleAvatar(
                              backgroundImage: user.avatarUrl != null ? NetworkImage(user.avatarUrl!) : null,
                              child: user.avatarUrl == null ? const Icon(Icons.person) : null,
                            ),
                            title: Text('@${user.username}'),
                            trailing: TextButton(
                              onPressed: () => _unblock(user),
                              child: const Text('Unblock'),
                            ),
                            onTap: () => Navigator.of(context).push(
                              MaterialPageRoute(builder: (_) => ProfileScreen(userId: user.id)),
                            ),
                          );
                        },
                      ),
      ),
    );
  }
}
