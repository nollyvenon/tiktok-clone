import 'package:flutter/material.dart';

import '../../models/message.dart';
import '../../services/message_service.dart';
import '../../services/auth_service.dart';
import 'chat_detail_screen.dart';

class MessagesScreen extends StatefulWidget {
  const MessagesScreen({super.key});

  @override
  State<MessagesScreen> createState() => _MessagesScreenState();
}

class _MessagesScreenState extends State<MessagesScreen> {
  final _messageService = MessageService();
  final List<Conversation> _conversations = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final conversations = await _messageService.getConversations();
      if (!mounted) return;
      setState(() {
        _conversations
          ..clear()
          ..addAll(conversations);
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

  String _timeAgo(DateTime dt) {
    final seconds = DateTime.now().difference(dt).inSeconds;
    if (seconds < 60) return '${seconds}s';
    final minutes = seconds ~/ 60;
    if (minutes < 60) return '${minutes}m';
    final hours = minutes ~/ 60;
    if (hours < 24) return '${hours}h';
    return '${hours ~/ 24}d';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Messages')),
      body: RefreshIndicator(
        onRefresh: _load,
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
                ? Center(child: Text(_error!))
                : _conversations.isEmpty
                    ? ListView(
                        children: const [
                          Padding(
                            padding: EdgeInsets.only(top: 120),
                            child: Center(
                              child: Text(
                                'No conversations yet.\nVisit a profile and tap message to start one.',
                                textAlign: TextAlign.center,
                                style: TextStyle(color: Colors.grey),
                              ),
                            ),
                          ),
                        ],
                      )
                    : ListView.builder(
                        itemCount: _conversations.length,
                        itemBuilder: (context, index) {
                          final conversation = _conversations[index];
                          return ListTile(
                            leading: CircleAvatar(
                              backgroundImage: conversation.otherUser.avatarUrl != null
                                  ? NetworkImage(conversation.otherUser.avatarUrl!)
                                  : null,
                              child: conversation.otherUser.avatarUrl == null
                                  ? const Icon(Icons.person)
                                  : null,
                            ),
                            title: Text('@${conversation.otherUser.username}'),
                            subtitle: Text(
                              conversation.lastMessage?.content ?? 'No messages yet',
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: TextStyle(
                                fontWeight: conversation.unreadCount > 0 ? FontWeight.bold : FontWeight.normal,
                                color: conversation.unreadCount > 0 ? Colors.black87 : Colors.grey,
                              ),
                            ),
                            trailing: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                Text(
                                  _timeAgo(conversation.updatedAt),
                                  style: const TextStyle(fontSize: 12, color: Colors.grey),
                                ),
                                if (conversation.unreadCount > 0)
                                  Container(
                                    margin: const EdgeInsets.only(top: 4),
                                    width: 8,
                                    height: 8,
                                    decoration: const BoxDecoration(color: Colors.pink, shape: BoxShape.circle),
                                  ),
                              ],
                            ),
                            onTap: () async {
                              await Navigator.of(context).push(
                                MaterialPageRoute(
                                  builder: (_) => ChatDetailScreen(
                                    conversationId: conversation.id,
                                    otherUsername: conversation.otherUser.username,
                                  ),
                                ),
                              );
                              _load();
                            },
                          );
                        },
                      ),
      ),
    );
  }
}
