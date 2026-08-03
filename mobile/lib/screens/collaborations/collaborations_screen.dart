import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/collaboration.dart';
import '../../models/video.dart';
import '../../models/user.dart';
import '../../providers/auth_provider.dart';
import '../../services/collaboration_service.dart';
import '../../services/feed_service.dart';
import '../../services/profile_service.dart';
import '../../services/auth_service.dart';

class CollaborationsScreen extends StatefulWidget {
  const CollaborationsScreen({super.key});

  @override
  State<CollaborationsScreen> createState() => _CollaborationsScreenState();
}

class _DraftCollaborator {
  final String userId;
  final String username;
  String percent = '';

  _DraftCollaborator({required this.userId, required this.username});
}

class _CollaborationsScreenState extends State<CollaborationsScreen> {
  final _collabService = CollaborationService();
  final _feedService = FeedService();
  final _profileService = ProfileService();

  List<Video> _myVideos = [];
  List<Collaboration> _collaborations = [];
  bool _isLoading = true;
  String? _error;

  String? _selectedVideoId;
  final _titleController = TextEditingController();
  final _ownPercentController = TextEditingController();
  final _inviteController = TextEditingController();
  List<User> _searchResults = [];
  final List<_DraftCollaborator> _drafts = [];
  bool _isCreating = false;
  String? _formError;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _titleController.dispose();
    _ownPercentController.dispose();
    _inviteController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final userId = context.read<AuthProvider>().user?.id;
      final results = await Future.wait([
        if (userId != null) _feedService.getUserVideos(userId) else Future.value(<Video>[]),
        _collabService.listMine(),
      ]);
      if (!mounted) return;
      setState(() {
        _myVideos = results[0] as List<Video>;
        _collaborations = results[1] as List<Collaboration>;
      });
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _searchUsers(String query) async {
    if (query.length < 2) {
      setState(() => _searchResults = []);
      return;
    }
    try {
      final results = await _profileService.searchCreators(query);
      if (mounted) setState(() => _searchResults = results);
    } on ApiException {
      // Non-critical: leave prior results in place
    }
  }

  void _addDraft(User user) {
    if (_drafts.any((d) => d.userId == user.id)) return;
    setState(() {
      _drafts.add(_DraftCollaborator(userId: user.id, username: user.username));
      _inviteController.clear();
      _searchResults = [];
    });
  }

  Future<void> _submitCreate() async {
    final userId = context.read<AuthProvider>().user?.id;
    if (userId == null || _selectedVideoId == null) {
      setState(() => _formError = 'Choose a video first');
      return;
    }
    setState(() {
      _isCreating = true;
      _formError = null;
    });
    try {
      final collaborators = [
        {'user_id': userId, 'revenue_split_percent': double.tryParse(_ownPercentController.text) ?? 0},
        ..._drafts.map((d) => {'user_id': d.userId, 'revenue_split_percent': double.tryParse(d.percent) ?? 0}),
      ];
      await _collabService.create(
        videoId: _selectedVideoId!,
        title: _titleController.text,
        collaborators: collaborators,
      );
      setState(() {
        _selectedVideoId = null;
        _titleController.clear();
        _ownPercentController.clear();
        _drafts.clear();
      });
      await _load();
    } on ApiException catch (e) {
      setState(() => _formError = e.message);
    } finally {
      if (mounted) setState(() => _isCreating = false);
    }
  }

  Future<void> _respond(String collaborationId, bool accept) async {
    try {
      await _collabService.respond(collaborationId, accept);
      await _load();
    } on ApiException catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  Future<void> _cancel(String collaborationId) async {
    try {
      await _collabService.cancel(collaborationId);
      await _load();
    } on ApiException catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Collaborations')),
      body: RefreshIndicator(
        onRefresh: _load,
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
                ? Center(child: Text(_error!))
                : _buildContent(),
      ),
    );
  }

  Widget _buildContent() {
    final userId = context.watch<AuthProvider>().user?.id;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text(
          'Invite other creators to collaborate on a video, with an agreed revenue split.',
          style: TextStyle(color: Colors.grey, fontSize: 13),
        ),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            border: Border.all(color: Colors.grey.shade300),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Start a collaboration', style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _selectedVideoId,
                decoration: const InputDecoration(labelText: 'Video', border: OutlineInputBorder()),
                items: _myVideos
                    .map((v) => DropdownMenuItem(value: v.id, child: Text(v.title ?? v.id, overflow: TextOverflow.ellipsis)))
                    .toList(),
                onChanged: (value) => setState(() => _selectedVideoId = value),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _titleController,
                decoration: const InputDecoration(labelText: 'Title (optional)', border: OutlineInputBorder()),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _ownPercentController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Your revenue share (%)', border: OutlineInputBorder()),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _inviteController,
                onChanged: _searchUsers,
                decoration: const InputDecoration(labelText: 'Search by username', border: OutlineInputBorder()),
              ),
              if (_searchResults.isNotEmpty)
                ..._searchResults.map((u) => ListTile(
                      dense: true,
                      contentPadding: EdgeInsets.zero,
                      title: Text('@${u.username}'),
                      onTap: () => _addDraft(u),
                    )),
              ..._drafts.map((d) => Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Row(
                      children: [
                        Expanded(child: Text('@${d.username}')),
                        SizedBox(
                          width: 70,
                          child: TextField(
                            keyboardType: TextInputType.number,
                            decoration: const InputDecoration(labelText: '%', isDense: true),
                            onChanged: (v) => d.percent = v,
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.close, size: 18),
                          onPressed: () => setState(() => _drafts.remove(d)),
                        ),
                      ],
                    ),
                  )),
              if (_formError != null) ...[
                const SizedBox(height: 8),
                Text(_formError!, style: const TextStyle(color: Colors.red)),
              ],
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isCreating ? null : _submitCreate,
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.pink, foregroundColor: Colors.white),
                  child: Text(_isCreating ? 'Creating...' : 'Create collaboration'),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 24),
        const Text('Your Collaborations', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        if (_collaborations.isEmpty)
          const Text('You have no collaborations yet.', style: TextStyle(color: Colors.grey))
        else
          ..._collaborations.map((collab) {
            CollaboratorSplit? mine;
            for (final c in collab.collaborators) {
              if (c.userId == userId) {
                mine = c;
                break;
              }
            }
            final isInitiator = collab.initiatorId == userId;
            final statusColor = collab.status == 'active'
                ? Colors.green
                : collab.status == 'cancelled'
                    ? Colors.grey
                    : Colors.orange;
            return Container(
              margin: const EdgeInsets.only(bottom: 12),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                border: Border.all(color: Colors.grey.shade300),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(collab.title ?? 'Untitled collaboration', style: const TextStyle(fontWeight: FontWeight.bold)),
                      Text(collab.status, style: TextStyle(color: statusColor, fontWeight: FontWeight.bold, fontSize: 12)),
                    ],
                  ),
                  const SizedBox(height: 6),
                  ...collab.collaborators.map((c) => Text(
                        '${c.userId == userId ? "You" : c.userId} — ${c.revenueSplitPercent}% (${c.status})',
                        style: const TextStyle(fontSize: 12, color: Colors.grey),
                      )),
                  const SizedBox(height: 8),
                  if (collab.status == 'pending' && mine?.status == 'invited')
                    Row(
                      children: [
                        TextButton(onPressed: () => _respond(collab.id, true), child: const Text('Accept')),
                        TextButton(
                          onPressed: () => _respond(collab.id, false),
                          child: const Text('Decline', style: TextStyle(color: Colors.red)),
                        ),
                      ],
                    ),
                  if (collab.status == 'pending' && isInitiator)
                    TextButton(onPressed: () => _cancel(collab.id), child: const Text('Cancel')),
                ],
              ),
            );
          }),
      ],
    );
  }
}
