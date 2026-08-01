import 'package:flutter/material.dart';

import '../../models/editor_state.dart';
import '../../services/editor_service.dart';

const _effects = ['blur', 'brighten', 'saturate', 'desaturate', 'vintage', 'cinematic'];

class EditorScreen extends StatefulWidget {
  final String draftId;

  const EditorScreen({super.key, required this.draftId});

  @override
  State<EditorScreen> createState() => _EditorScreenState();
}

class _EditorScreenState extends State<EditorScreen> {
  final _editorService = EditorService();
  EditorStateData? _state;
  bool _isLoading = true;
  String? _error;
  String? _busySegmentId;
  String? _exportStatus;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final state = await _editorService.getEditorState(widget.draftId);
      setState(() => _state = state);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _withBusy(String segmentId, Future<void> Function() action) async {
    setState(() => _busySegmentId = segmentId);
    try {
      await action();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
    } finally {
      setState(() => _busySegmentId = null);
    }
  }

  Future<void> _applyEffect(EditorSegment segment, String effect) => _withBusy(segment.id, () async {
        final updated = await _editorService.applyEffect(segment.id, effect);
        setState(() => segment.effects = updated.effects);
      });

  Future<void> _deleteSegment(EditorSegment segment) => _withBusy(segment.id, () async {
        await _editorService.deleteSegment(segment.id);
        setState(() => _state?.segments.remove(segment));
      });

  Future<void> _toggleMute(EditorSegment segment) => _withBusy(segment.id, () async {
        final updated = await _editorService.muteSegment(segment.id, !segment.muted);
        setState(() => segment.muted = updated.muted);
      });

  Future<void> _addTextOverlay(EditorSegment segment) async {
    final controller = TextEditingController();
    final text = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add text overlay'),
        content: TextField(controller: controller, autofocus: true),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          TextButton(
            onPressed: () => Navigator.pop(context, controller.text),
            child: const Text('Add'),
          ),
        ],
      ),
    );
    if (text == null || text.isEmpty) return;
    try {
      await _editorService.addTextOverlay(segment.id, text);
      await _load();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
    }
  }

  Future<void> _export() async {
    setState(() => _exportStatus = 'Queuing export...');
    try {
      final result = await _editorService.exportVideo(widget.draftId);
      setState(() => _exportStatus = 'Export ${result['status']} (${result['quality']}, ${result['format']})');
    } catch (e) {
      setState(() => _exportStatus = 'Export failed: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Edit video'),
        actions: [
          IconButton(icon: const Icon(Icons.file_download), onPressed: _export),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    if (_exportStatus != null) ...[
                      Text(_exportStatus!, style: Theme.of(context).textTheme.bodySmall),
                      const SizedBox(height: 12),
                    ],
                    Text(
                      'Total duration: ${((_state?.totalDuration ?? 0) / 1000).toStringAsFixed(1)}s '
                      '· ${_state?.textOverlayCount ?? 0} text overlay(s)',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    const SizedBox(height: 16),
                    ...(_state?.segments ?? []).map((segment) {
                      final isBusy = _busySegmentId == segment.id;
                      return Card(
                        margin: const EdgeInsets.only(bottom: 12),
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Text(
                                    'Segment ${segment.order + 1} · ${segment.contentType}',
                                    style: const TextStyle(fontWeight: FontWeight.bold),
                                  ),
                                  IconButton(
                                    icon: const Icon(Icons.delete, color: Colors.red),
                                    onPressed: isBusy ? null : () => _deleteSegment(segment),
                                  ),
                                ],
                              ),
                              Wrap(
                                spacing: 8,
                                children: _effects
                                    .map((effect) => ActionChip(
                                          label: Text(effect),
                                          onPressed: isBusy ? null : () => _applyEffect(segment, effect),
                                        ))
                                    .toList(),
                              ),
                              if (segment.effects.isNotEmpty) ...[
                                const SizedBox(height: 8),
                                Wrap(
                                  spacing: 8,
                                  children: segment.effects
                                      .map((e) => Chip(
                                            label: Text(e),
                                            backgroundColor: Colors.pink.shade50,
                                          ))
                                      .toList(),
                                ),
                              ],
                              const SizedBox(height: 8),
                              Row(
                                children: [
                                  TextButton.icon(
                                    onPressed: isBusy ? null : () => _toggleMute(segment),
                                    icon: Icon(segment.muted ? Icons.volume_off : Icons.volume_up),
                                    label: Text(segment.muted ? 'Unmute' : 'Mute'),
                                  ),
                                  TextButton.icon(
                                    onPressed: () => _addTextOverlay(segment),
                                    icon: const Icon(Icons.text_fields),
                                    label: const Text('Add text'),
                                  ),
                                ],
                              ),
                              Text(
                                '${segment.startTime}ms - ${segment.endTime}ms',
                                style: Theme.of(context).textTheme.bodySmall,
                              ),
                            ],
                          ),
                        ),
                      );
                    }),
                    if ((_state?.segments ?? []).isEmpty)
                      const Center(child: Text('No segments yet')),
                  ],
                ),
    );
  }
}
