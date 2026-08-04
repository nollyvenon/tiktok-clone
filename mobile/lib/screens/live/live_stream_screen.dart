import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/live_stream.dart';
import '../../providers/auth_provider.dart';
import '../../services/live_streaming_service.dart';
import '../../services/auth_service.dart';

class LiveStreamScreen extends StatefulWidget {
  final String streamId;

  const LiveStreamScreen({super.key, required this.streamId});

  @override
  State<LiveStreamScreen> createState() => _LiveStreamScreenState();
}

class _LiveStreamScreenState extends State<LiveStreamScreen> {
  final _liveService = LiveStreamingService();
  final _chatController = TextEditingController();
  LiveStream? _stream;
  List<LiveChatMessage> _messages = [];
  bool _isLoading = true;
  String? _error;
  bool _hasJoined = false;
  Timer? _streamTimer;
  Timer? _chatTimer;

  @override
  void initState() {
    super.initState();
    _load();
    _join();
    _streamTimer = Timer.periodic(const Duration(seconds: 5), (_) => _refreshStream());
    _chatTimer = Timer.periodic(const Duration(seconds: 3), (_) => _refreshChat());
  }

  @override
  void dispose() {
    _streamTimer?.cancel();
    _chatTimer?.cancel();
    if (_hasJoined) _liveService.leaveStream(widget.streamId);
    _chatController.dispose();
    super.dispose();
  }

  Future<void> _join() async {
    try {
      await _liveService.joinStream(widget.streamId);
      _hasJoined = true;
    } on ApiException {
      // Stream may have already ended - viewing still works, join is best-effort
    }
  }

  Future<void> _load() async {
    setState(() => _isLoading = true);
    try {
      final results = await Future.wait([
        _liveService.getStream(widget.streamId),
        _liveService.getChatMessages(widget.streamId),
      ]);
      if (!mounted) return;
      setState(() {
        _stream = results[0] as LiveStream;
        _messages = results[1] as List<LiveChatMessage>;
      });
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _refreshStream() async {
    try {
      final stream = await _liveService.getStream(widget.streamId);
      if (mounted) setState(() => _stream = stream);
    } on ApiException {
      // Ignore transient polling failures
    }
  }

  Future<void> _refreshChat() async {
    try {
      final messages = await _liveService.getChatMessages(widget.streamId);
      if (mounted) setState(() => _messages = messages);
    } on ApiException {
      // Ignore transient polling failures
    }
  }

  Future<void> _sendMessage() async {
    if (_chatController.text.isEmpty) return;
    final content = _chatController.text;
    _chatController.clear();
    try {
      await _liveService.postChatMessage(widget.streamId, content);
      await _refreshChat();
    } on ApiException catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  Future<void> _endStream() async {
    try {
      await _liveService.endStream(widget.streamId);
      if (mounted) Navigator.of(context).pop();
    } on ApiException catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  @override
  Widget build(BuildContext context) {
    final userId = context.watch<AuthProvider>().user?.id;
    final isOwner = _stream != null && _stream!.creatorId == userId;

    return Scaffold(
      appBar: AppBar(
        title: Text(_stream?.title ?? 'Live'),
        actions: [
          if (isOwner && _stream?.status == 'live')
            TextButton(
              onPressed: _endStream,
              child: const Text('End', style: TextStyle(color: Colors.red)),
            ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : _buildContent(),
    );
  }

  Widget _buildContent() {
    final stream = _stream!;
    return Column(
      children: [
        Container(
          height: 200,
          margin: const EdgeInsets.all(16),
          decoration: BoxDecoration(color: Colors.grey.shade900, borderRadius: BorderRadius.circular(8)),
          child: const Center(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Text(
                'No video preview in this build - live chat and viewer presence are fully functional below.',
                style: TextStyle(color: Colors.grey),
                textAlign: TextAlign.center,
              ),
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            children: [
              if (stream.status == 'live')
                const Text('● LIVE', style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold))
              else
                const Text('Ended', style: TextStyle(color: Colors.grey, fontWeight: FontWeight.bold)),
              const SizedBox(width: 12),
              Text('${stream.viewerCount} watching', style: const TextStyle(color: Colors.grey)),
            ],
          ),
        ),
        const Divider(),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            itemCount: _messages.length,
            itemBuilder: (context, index) {
              final message = _messages[index];
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 2),
                child: RichText(
                  text: TextSpan(
                    style: DefaultTextStyle.of(context).style,
                    children: [
                      TextSpan(text: '@${message.username} ', style: const TextStyle(fontWeight: FontWeight.bold)),
                      TextSpan(text: message.content),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
        if (stream.status == 'live')
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _chatController,
                    onSubmitted: (_) => _sendMessage(),
                    decoration: const InputDecoration(hintText: 'Say something...', isDense: true),
                  ),
                ),
                IconButton(icon: const Icon(Icons.send), onPressed: _sendMessage),
              ],
            ),
          ),
      ],
    );
  }
}
