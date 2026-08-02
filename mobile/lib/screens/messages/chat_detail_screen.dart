import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/message.dart';
import '../../providers/auth_provider.dart';
import '../../services/message_service.dart';
import '../../services/auth_service.dart';

class ChatDetailScreen extends StatefulWidget {
  final String conversationId;
  final String otherUsername;

  const ChatDetailScreen({
    super.key,
    required this.conversationId,
    required this.otherUsername,
  });

  @override
  State<ChatDetailScreen> createState() => _ChatDetailScreenState();
}

// No WebSocket transport exists yet anywhere in this app, so new messages
// are picked up via short polling rather than a live push - the same
// known gap documented for the notification system.
const _pollInterval = Duration(seconds: 4);

class _ChatDetailScreenState extends State<ChatDetailScreen> {
  final _messageService = MessageService();
  final _inputController = TextEditingController();
  final _scrollController = ScrollController();
  final List<ChatMessage> _messages = [];
  Timer? _pollTimer;
  bool _isLoading = true;
  String? _error;
  bool _isSending = false;

  @override
  void initState() {
    super.initState();
    _load();
    _messageService.markRead(widget.conversationId).catchError((_) {});
    _pollTimer = Timer.periodic(_pollInterval, (_) => _load(silent: true));
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    _inputController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _load({bool silent = false}) async {
    if (!silent) setState(() => _isLoading = true);
    try {
      final messages = await _messageService.getMessages(widget.conversationId);
      if (!mounted) return;
      setState(() {
        _messages
          ..clear()
          ..addAll(messages);
        _isLoading = false;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      if (!silent) setState(() => _error = e.message);
    }
  }

  Future<void> _send() async {
    final content = _inputController.text.trim();
    if (content.isEmpty || _isSending) return;
    _inputController.clear();
    setState(() => _isSending = true);
    try {
      final message = await _messageService.sendMessage(widget.conversationId, content);
      if (!mounted) return;
      setState(() {
        _messages.add(message);
        _isSending = false;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() => _isSending = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  @override
  Widget build(BuildContext context) {
    final currentUserId = context.watch<AuthProvider>().user?.id;

    return Scaffold(
      appBar: AppBar(title: Text('@${widget.otherUsername}')),
      body: Column(
        children: [
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _error != null
                    ? Center(child: Text(_error!))
                    : _messages.isEmpty
                        ? const Center(child: Text('No messages yet. Say hello!'))
                        : ListView.builder(
                            controller: _scrollController,
                            padding: const EdgeInsets.all(12),
                            itemCount: _messages.length,
                            itemBuilder: (context, index) {
                              final message = _messages[index];
                              final isOwn = message.senderId == currentUserId;
                              return Align(
                                alignment: isOwn ? Alignment.centerRight : Alignment.centerLeft,
                                child: Container(
                                  margin: const EdgeInsets.symmetric(vertical: 4),
                                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                                  constraints: BoxConstraints(
                                    maxWidth: MediaQuery.of(context).size.width * 0.7,
                                  ),
                                  decoration: BoxDecoration(
                                    color: isOwn ? Colors.pink : Colors.grey.shade200,
                                    borderRadius: BorderRadius.circular(16),
                                  ),
                                  child: Text(
                                    message.content,
                                    style: TextStyle(color: isOwn ? Colors.white : Colors.black87),
                                  ),
                                ),
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
                        hintText: 'Type a message...',
                        border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(24))),
                        contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      ),
                      onSubmitted: (_) => _send(),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.send),
                    onPressed: _isSending ? null : _send,
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
