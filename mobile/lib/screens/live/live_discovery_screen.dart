import 'dart:async';

import 'package:flutter/material.dart';

import '../../models/live_stream.dart';
import '../../services/live_streaming_service.dart';
import '../../services/auth_service.dart';
import 'live_stream_screen.dart';

class LiveDiscoveryScreen extends StatefulWidget {
  const LiveDiscoveryScreen({super.key});

  @override
  State<LiveDiscoveryScreen> createState() => _LiveDiscoveryScreenState();
}

class _LiveDiscoveryScreenState extends State<LiveDiscoveryScreen> {
  final _liveService = LiveStreamingService();
  final _titleController = TextEditingController();
  List<LiveStream> _streams = [];
  bool _isLoading = true;
  String? _error;
  String? _startError;
  bool _isStarting = false;
  Timer? _refreshTimer;

  @override
  void initState() {
    super.initState();
    _load();
    _refreshTimer = Timer.periodic(const Duration(seconds: 10), (_) => _load(silent: true));
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    _titleController.dispose();
    super.dispose();
  }

  Future<void> _load({bool silent = false}) async {
    if (!silent) setState(() => _isLoading = true);
    try {
      final streams = await _liveService.listLiveStreams();
      if (!mounted) return;
      setState(() => _streams = streams);
    } on ApiException catch (e) {
      if (mounted && !silent) setState(() => _error = e.message);
    } finally {
      if (mounted && !silent) setState(() => _isLoading = false);
    }
  }

  Future<void> _goLive() async {
    setState(() {
      _isStarting = true;
      _startError = null;
    });
    try {
      final stream = await _liveService.startStream(_titleController.text);
      if (!mounted) return;
      Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => LiveStreamScreen(streamId: stream.id)),
      );
    } on ApiException catch (e) {
      setState(() => _startError = e.message);
    } finally {
      if (mounted) setState(() => _isStarting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Live')),
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
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            border: Border.all(color: Colors.grey.shade300),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Go live', style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _titleController,
                      decoration: const InputDecoration(labelText: 'Stream title', isDense: true),
                    ),
                  ),
                  const SizedBox(width: 8),
                  ElevatedButton(
                    onPressed: _isStarting ? null : _goLive,
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.pink, foregroundColor: Colors.white),
                    child: const Text('Start'),
                  ),
                ],
              ),
              if (_startError != null) ...[
                const SizedBox(height: 8),
                Text(_startError!, style: const TextStyle(color: Colors.red, fontSize: 12)),
              ],
            ],
          ),
        ),
        const SizedBox(height: 24),
        const Text('Live now', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        const SizedBox(height: 8),
        if (_streams.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 24),
            child: Text('No one is live right now.', style: TextStyle(color: Colors.grey)),
          )
        else
          ..._streams.map((stream) => Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: ListTile(
                  leading: const CircleAvatar(
                    backgroundColor: Colors.red,
                    child: Icon(Icons.circle, color: Colors.white, size: 10),
                  ),
                  title: Text(stream.title),
                  subtitle: Text('${stream.viewerCount} watching'),
                  onTap: () => Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => LiveStreamScreen(streamId: stream.id)),
                  ),
                ),
              )),
      ],
    );
  }
}
