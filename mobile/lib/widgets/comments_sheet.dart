import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/comment.dart';
import '../providers/auth_provider.dart';
import '../services/comment_service.dart';
import '../services/auth_service.dart';
import 'report_sheet.dart';

String _timeAgo(DateTime dt) {
  final seconds = DateTime.now().difference(dt).inSeconds;
  if (seconds < 60) return '${seconds}s';
  final minutes = seconds ~/ 60;
  if (minutes < 60) return '${minutes}m';
  final hours = minutes ~/ 60;
  if (hours < 24) return '${hours}h';
  return '${hours ~/ 24}d';
}

class CommentsSheet extends StatefulWidget {
  final String videoId;
  final String videoOwnerId;
  final void Function(int delta) onCommentCountChanged;

  const CommentsSheet({
    super.key,
    required this.videoId,
    required this.videoOwnerId,
    required this.onCommentCountChanged,
  });

  static Future<void> show(
    BuildContext context, {
    required String videoId,
    required String videoOwnerId,
    required void Function(int delta) onCommentCountChanged,
  }) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => CommentsSheet(
        videoId: videoId,
        videoOwnerId: videoOwnerId,
        onCommentCountChanged: onCommentCountChanged,
      ),
    );
  }

  @override
  State<CommentsSheet> createState() => _CommentsSheetState();
}

class _CommentsSheetState extends State<CommentsSheet> {
  final _commentService = CommentService();
  final _inputController = TextEditingController();
  final List<Comment> _comments = [];
  bool _isLoading = true;
  int _total = 0;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _isLoading = true);
    try {
      final page = await _commentService.getComments(widget.videoId);
      if (!mounted) return;
      setState(() {
        _comments
          ..clear()
          ..addAll(page.comments);
        _total = page.total;
        _isLoading = false;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.message;
        _isLoading = false;
      });
    }
  }

  Future<void> _postComment() async {
    final content = _inputController.text.trim();
    if (content.isEmpty) return;
    _inputController.clear();
    try {
      final comment = await _commentService.createComment(widget.videoId, content);
      if (!mounted) return;
      setState(() {
        _comments.insert(0, comment);
        _total += 1;
      });
      widget.onCommentCountChanged(1);
    } on ApiException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  Future<void> _delete(Comment comment) async {
    try {
      await _commentService.deleteComment(comment.id);
      if (!mounted) return;
      setState(() {
        _comments.remove(comment);
        _total -= 1;
      });
      widget.onCommentCountChanged(-1);
    } on ApiException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  @override
  Widget build(BuildContext context) {
    final currentUserId = context.watch<AuthProvider>().user?.id;

    return DraggableScrollableSheet(
      initialChildSize: 0.65,
      minChildSize: 0.4,
      maxChildSize: 0.95,
      expand: false,
      builder: (context, scrollController) {
        return Container(
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
          ),
          child: Column(
            children: [
              const SizedBox(height: 8),
              Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.grey.shade300, borderRadius: BorderRadius.circular(2))),
              Padding(
                padding: const EdgeInsets.all(12),
                child: Text('$_total comments', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              ),
              const Divider(height: 1),
              Expanded(
                child: _isLoading
                    ? const Center(child: CircularProgressIndicator())
                    : _error != null
                        ? Center(child: Text(_error!))
                        : _comments.isEmpty
                            ? const Center(child: Text('No comments yet. Be the first!'))
                            : ListView.builder(
                                controller: scrollController,
                                itemCount: _comments.length,
                                itemBuilder: (context, index) {
                                  final comment = _comments[index];
                                  return _CommentTile(
                                    comment: comment,
                                    videoId: widget.videoId,
                                    videoOwnerId: widget.videoOwnerId,
                                    currentUserId: currentUserId,
                                    onDelete: () => _delete(comment),
                                  );
                                },
                              ),
              ),
              SafeArea(
                top: false,
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  child: Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _inputController,
                          decoration: const InputDecoration(
                            hintText: 'Add a comment...',
                            border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(24))),
                            contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                          ),
                          onSubmitted: (_) => _postComment(),
                        ),
                      ),
                      IconButton(icon: const Icon(Icons.send), onPressed: _postComment),
                    ],
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _CommentTile extends StatefulWidget {
  final Comment comment;
  final String videoId;
  final String videoOwnerId;
  final String? currentUserId;
  final VoidCallback onDelete;
  final bool isReply;

  const _CommentTile({
    required this.comment,
    required this.videoId,
    required this.videoOwnerId,
    required this.currentUserId,
    required this.onDelete,
    this.isReply = false,
  });

  @override
  State<_CommentTile> createState() => _CommentTileState();
}

class _CommentTileState extends State<_CommentTile> {
  final _commentService = CommentService();
  final _replyController = TextEditingController();
  bool _isReplying = false;
  bool _showReplies = false;
  List<Comment> _replies = [];
  bool _repliesLoaded = false;

  bool get _isOwnComment => widget.currentUserId == widget.comment.userId;
  bool get _isVideoOwner => widget.currentUserId == widget.videoOwnerId;

  Future<void> _toggleLike() async {
    try {
      final result = await _commentService.toggleLike(widget.comment.id);
      if (!mounted) return;
      setState(() {
        widget.comment.isLiked = result['is_liked'] as bool;
        widget.comment.likesCount = result['likes_count'] as int;
      });
    } on ApiException catch (_) {}
  }

  Future<void> _togglePin() async {
    try {
      final updated = await _commentService.togglePin(widget.comment.id);
      if (!mounted) return;
      setState(() => widget.comment.isPinned = updated.isPinned);
    } on ApiException catch (_) {}
  }

  Future<void> _loadReplies() async {
    try {
      final page = await _commentService.getReplies(widget.comment.id);
      if (!mounted) return;
      setState(() {
        _replies = page.comments;
        _repliesLoaded = true;
      });
    } on ApiException catch (_) {}
  }

  Future<void> _deleteReply(Comment reply) async {
    try {
      await _commentService.deleteComment(reply.id);
      if (!mounted) return;
      setState(() {
        _replies.remove(reply);
        widget.comment.repliesCount -= 1;
      });
    } on ApiException catch (_) {}
  }

  Future<void> _postReply() async {
    final content = _replyController.text.trim();
    if (content.isEmpty) return;
    _replyController.clear();
    try {
      final reply = await _commentService.createComment(
        widget.videoId,
        content,
        parentCommentId: widget.comment.id,
      );
      if (!mounted) return;
      setState(() {
        widget.comment.repliesCount += 1;
        _replies.add(reply);
        _showReplies = true;
        _repliesLoaded = true;
        _isReplying = false;
      });
    } on ApiException catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    final comment = widget.comment;
    return Padding(
      padding: EdgeInsets.only(left: widget.isReply ? 48 : 16, right: 16, top: 8, bottom: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              CircleAvatar(
                radius: 16,
                backgroundImage: comment.user.avatarUrl != null ? NetworkImage(comment.user.avatarUrl!) : null,
                child: comment.user.avatarUrl == null ? const Icon(Icons.person, size: 16) : null,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text('@${comment.user.username}', style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                        if (comment.isPinned) ...[
                          const SizedBox(width: 6),
                          const Icon(Icons.push_pin, size: 12, color: Colors.grey),
                        ],
                        const SizedBox(width: 6),
                        Text(_timeAgo(comment.createdAt), style: const TextStyle(color: Colors.grey, fontSize: 11)),
                      ],
                    ),
                    const SizedBox(height: 2),
                    Text(comment.content, style: const TextStyle(fontSize: 14)),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        InkWell(
                          onTap: _toggleLike,
                          child: Row(
                            children: [
                              Icon(comment.isLiked ? Icons.favorite : Icons.favorite_border,
                                  size: 14, color: comment.isLiked ? Colors.red : Colors.grey),
                              if (comment.likesCount > 0) ...[
                                const SizedBox(width: 4),
                                Text('${comment.likesCount}', style: const TextStyle(fontSize: 11, color: Colors.grey)),
                              ],
                            ],
                          ),
                        ),
                        if (!widget.isReply) ...[
                          const SizedBox(width: 16),
                          InkWell(
                            onTap: () => setState(() => _isReplying = !_isReplying),
                            child: const Text('Reply', style: TextStyle(fontSize: 11, color: Colors.grey)),
                          ),
                        ],
                        if (_isOwnComment || _isVideoOwner) ...[
                          const SizedBox(width: 16),
                          InkWell(
                            onTap: widget.onDelete,
                            child: const Icon(Icons.delete_outline, size: 14, color: Colors.grey),
                          ),
                        ],
                        if (!_isOwnComment) ...[
                          const SizedBox(width: 16),
                          InkWell(
                            onTap: () => ReportSheet.show(context, contentType: 'comment', contentId: comment.id),
                            child: const Icon(Icons.flag_outlined, size: 14, color: Colors.grey),
                          ),
                        ],
                        if (!widget.isReply && _isVideoOwner) ...[
                          const SizedBox(width: 16),
                          InkWell(
                            onTap: _togglePin,
                            child: Text(comment.isPinned ? 'Unpin' : 'Pin', style: const TextStyle(fontSize: 11, color: Colors.grey)),
                          ),
                        ],
                        if (!widget.isReply && comment.repliesCount > 0) ...[
                          const SizedBox(width: 16),
                          InkWell(
                            onTap: () {
                              setState(() => _showReplies = !_showReplies);
                              if (_showReplies && !_repliesLoaded) _loadReplies();
                            },
                            child: Text(
                              '${_showReplies ? 'Hide' : 'View'} ${comment.repliesCount} ${comment.repliesCount == 1 ? 'reply' : 'replies'}',
                              style: const TextStyle(fontSize: 11, color: Colors.blue, fontWeight: FontWeight.w600),
                            ),
                          ),
                        ],
                      ],
                    ),
                    if (_isReplying)
                      Padding(
                        padding: const EdgeInsets.only(top: 6),
                        child: Row(
                          children: [
                            Expanded(
                              child: TextField(
                                controller: _replyController,
                                style: const TextStyle(fontSize: 13),
                                decoration: InputDecoration(
                                  hintText: 'Reply to @${comment.user.username}',
                                  isDense: true,
                                  border: const OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(20))),
                                  contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                ),
                                onSubmitted: (_) => _postReply(),
                              ),
                            ),
                            IconButton(icon: const Icon(Icons.send, size: 18), onPressed: _postReply),
                          ],
                        ),
                      ),
                  ],
                ),
              ),
            ],
          ),
          if (_showReplies)
            ..._replies.map((reply) => _CommentTile(
                  comment: reply,
                  videoId: widget.videoId,
                  videoOwnerId: widget.videoOwnerId,
                  currentUserId: widget.currentUserId,
                  onDelete: () => _deleteReply(reply),
                  isReply: true,
                )),
        ],
      ),
    );
  }
}
