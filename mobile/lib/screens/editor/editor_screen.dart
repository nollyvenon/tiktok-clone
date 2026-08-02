import 'package:flutter/material.dart';

import '../../models/editor_state.dart';
import '../../services/ai_service.dart';
import '../../services/editor_service.dart';
import '../../services/upload_service.dart';

const _effects = ['blur', 'brighten', 'saturate', 'desaturate', 'vintage', 'cinematic'];
const _voices = [
  {'id': 'en-US-female-1', 'label': 'English (US) — Female'},
  {'id': 'en-US-male-1', 'label': 'English (US) — Male'},
  {'id': 'en-GB-female-1', 'label': 'English (UK) — Female'},
  {'id': 'es-ES-female-1', 'label': 'Spanish — Female'},
];

class EditorScreen extends StatefulWidget {
  final String draftId;

  const EditorScreen({super.key, required this.draftId});

  @override
  State<EditorScreen> createState() => _EditorScreenState();
}

class _EditorScreenState extends State<EditorScreen> {
  final _editorService = EditorService();
  final _aiService = AIService();
  final _uploadService = UploadService();
  EditorStateData? _state;
  bool _isLoading = true;
  String? _error;
  String? _busySegmentId;
  String? _exportStatus;
  final Map<String, String> _aiStatus = {};
  final Map<String, List<Map<String, dynamic>>> _stickersBySegment = {};
  List<SoundRecommendation> _sounds = [];
  bool _soundsLoading = false;
  bool _soundsLoaded = false;
  String? _selectedSoundId;

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
      final stickerEntries = await Future.wait(
        state.segments.map((s) async => MapEntry(s.id, await _editorService.getStickers(s.id))),
      );
      final draft = await _uploadService.getDraft(widget.draftId);
      setState(() {
        _state = state;
        _stickersBySegment
          ..clear()
          ..addEntries(stickerEntries);
        _selectedSoundId = draft.musicId;
      });
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

  Future<void> _generateVoiceover(EditorSegment segment) async {
    final textController = TextEditingController();
    String selectedVoiceId = _voices.first['id']!;

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Generate voiceover'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: textController,
                autofocus: true,
                maxLines: 3,
                decoration: const InputDecoration(hintText: 'Voiceover script'),
              ),
              const SizedBox(height: 12),
              DropdownButton<String>(
                value: selectedVoiceId,
                isExpanded: true,
                items: _voices
                    .map((v) => DropdownMenuItem(value: v['id'], child: Text(v['label']!)))
                    .toList(),
                onChanged: (value) => setDialogState(() => selectedVoiceId = value!),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
            TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('Generate')),
          ],
        ),
      ),
    );

    if (confirmed != true || textController.text.isEmpty) return;

    setState(() => _aiStatus[segment.id] = 'Generating voiceover... (15 credits)');
    try {
      await _aiService.generateVoiceover(segment.id, textController.text, selectedVoiceId);
      setState(() => _aiStatus[segment.id] = 'Voiceover queued');
    } catch (e) {
      setState(() => _aiStatus[segment.id] = e.toString());
    }
  }

  Future<void> _loadSounds([String? category]) async {
    setState(() => _soundsLoading = true);
    try {
      final sounds = await _aiService.getSoundRecommendations(category: category);
      setState(() {
        _sounds = sounds;
        _soundsLoaded = true;
      });
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
    } finally {
      setState(() => _soundsLoading = false);
    }
  }

  Future<void> _useSound(String soundId) async {
    try {
      final draft = await _uploadService.getDraft(widget.draftId);
      await _uploadService.updateDraft(widget.draftId, draft.copyWith(musicId: soundId));
      setState(() => _selectedSoundId = soundId);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to attach sound: $e')),
        );
      }
    }
  }

  Future<void> _addSticker(EditorSegment segment) async {
    final controller = TextEditingController();
    final url = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add sticker'),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: const InputDecoration(hintText: 'Sticker image URL'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          TextButton(onPressed: () => Navigator.pop(context, controller.text), child: const Text('Add')),
        ],
      ),
    );
    if (url == null || url.isEmpty) return;
    try {
      await _editorService.addSticker(segment.id, url);
      await _load();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
    }
  }

  Future<void> _deleteSticker(String stickerId) async {
    try {
      await _editorService.deleteSticker(stickerId);
      await _load();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
    }
  }

  Future<void> _moveSegment(int index, int direction) async {
    final segments = _state?.segments;
    if (segments == null) return;
    final newIndex = index + direction;
    if (newIndex < 0 || newIndex >= segments.length) return;

    setState(() {
      final segment = segments.removeAt(index);
      segments.insert(newIndex, segment);
    });

    try {
      await _editorService.reorderSegments(widget.draftId, segments.map((s) => s.id).toList());
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
      await _load();
    }
  }

  Future<void> _removeBackground(EditorSegment segment) async {
    setState(() => _aiStatus[segment.id] = 'Removing background... (10 credits)');
    try {
      await _aiService.removeBackground(segment.id);
      setState(() => _aiStatus[segment.id] = 'Background removal queued');
    } catch (e) {
      setState(() => _aiStatus[segment.id] = e.toString());
    }
  }

  Future<void> _generateCaptions(EditorSegment segment) async {
    setState(() => _aiStatus[segment.id] = 'Generating captions... (5 credits)');
    try {
      await _aiService.generateCaptions(segment.id);
      setState(() => _aiStatus[segment.id] = 'Captions queued');
    } catch (e) {
      setState(() => _aiStatus[segment.id] = e.toString());
    }
  }

  Future<void> _colorCorrect(EditorSegment segment) async {
    setState(() => _aiStatus[segment.id] = 'Applying auto color correction...');
    try {
      await _aiService.applyColorCorrection(segment.id);
      setState(() => _aiStatus[segment.id] = 'Color correction queued');
    } catch (e) {
      setState(() => _aiStatus[segment.id] = e.toString());
    }
  }

  Future<void> _smartFrame(EditorSegment segment) async {
    setState(() => _aiStatus[segment.id] = 'Getting frame suggestions...');
    try {
      await _aiService.getFrameSuggestions(segment.id);
      setState(() => _aiStatus[segment.id] = 'Smart framing queued');
    } catch (e) {
      setState(() => _aiStatus[segment.id] = e.toString());
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
                    ...(_state?.segments ?? []).asMap().entries.map((entry) {
                      final index = entry.key;
                      final segment = entry.value;
                      final isBusy = _busySegmentId == segment.id;
                      final stickers = _stickersBySegment[segment.id] ?? [];
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
                                  Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      IconButton(
                                        icon: const Icon(Icons.arrow_upward),
                                        onPressed: (isBusy || index == 0)
                                            ? null
                                            : () => _moveSegment(index, -1),
                                      ),
                                      IconButton(
                                        icon: const Icon(Icons.arrow_downward),
                                        onPressed: (isBusy || index == (_state?.segments.length ?? 0) - 1)
                                            ? null
                                            : () => _moveSegment(index, 1),
                                      ),
                                      IconButton(
                                        icon: const Icon(Icons.delete, color: Colors.red),
                                        onPressed: isBusy ? null : () => _deleteSegment(segment),
                                      ),
                                    ],
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
                                  TextButton.icon(
                                    onPressed: () => _addSticker(segment),
                                    icon: const Icon(Icons.emoji_emotions_outlined),
                                    label: const Text('Add sticker'),
                                  ),
                                ],
                              ),
                              if (stickers.isNotEmpty)
                                Wrap(
                                  spacing: 8,
                                  children: stickers.map((sticker) {
                                    return Chip(
                                      label: Text(sticker['sticker_type'] as String? ?? 'sticker'),
                                      deleteIcon: const Icon(Icons.close, size: 16),
                                      onDeleted: () => _deleteSticker(sticker['id'] as String),
                                    );
                                  }).toList(),
                                ),
                              Text(
                                '${segment.startTime}ms - ${segment.endTime}ms',
                                style: Theme.of(context).textTheme.bodySmall,
                              ),
                              const Divider(),
                              const Row(
                                children: [
                                  Icon(Icons.auto_awesome, size: 14, color: Colors.purple),
                                  SizedBox(width: 4),
                                  Text('AI tools', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                                ],
                              ),
                              const SizedBox(height: 4),
                              Wrap(
                                spacing: 8,
                                children: [
                                  ActionChip(
                                    label: const Text('Remove background'),
                                    onPressed: () => _removeBackground(segment),
                                  ),
                                  ActionChip(
                                    label: const Text('Auto captions'),
                                    onPressed: () => _generateCaptions(segment),
                                  ),
                                  ActionChip(
                                    label: const Text('Auto color'),
                                    onPressed: () => _colorCorrect(segment),
                                  ),
                                  ActionChip(
                                    label: const Text('Smart frame'),
                                    onPressed: () => _smartFrame(segment),
                                  ),
                                  ActionChip(
                                    avatar: const Icon(Icons.mic, size: 16),
                                    label: const Text('Voiceover'),
                                    onPressed: () => _generateVoiceover(segment),
                                  ),
                                ],
                              ),
                              if (_aiStatus[segment.id] != null)
                                Padding(
                                  padding: const EdgeInsets.only(top: 4),
                                  child: Text(
                                    _aiStatus[segment.id]!,
                                    style: Theme.of(context).textTheme.bodySmall,
                                  ),
                                ),
                            ],
                          ),
                        ),
                      );
                    }),
                    if ((_state?.segments ?? []).isEmpty)
                      const Center(child: Text('No segments yet')),
                    const Divider(height: 32),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Row(
                          children: [
                            Icon(Icons.music_note, size: 18),
                            SizedBox(width: 6),
                            Text('Sound recommendations', style: TextStyle(fontWeight: FontWeight.bold)),
                          ],
                        ),
                        if (!_soundsLoaded)
                          TextButton(
                            onPressed: _soundsLoading ? null : () => _loadSounds(),
                            child: Text(_soundsLoading ? 'Loading...' : 'Browse sounds'),
                          ),
                      ],
                    ),
                    if (_soundsLoaded) ...[
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 8,
                        children: ['background', 'sound_effect', 'music', 'ambient']
                            .map((cat) => ActionChip(
                                  label: Text(cat.replaceAll('_', ' ')),
                                  onPressed: () => _loadSounds(cat),
                                ))
                            .toList(),
                      ),
                      const SizedBox(height: 8),
                      if (_sounds.isEmpty)
                        const Text('No sounds found', style: TextStyle(color: Colors.grey))
                      else
                        ..._sounds.map((sound) => ListTile(
                              dense: true,
                              contentPadding: EdgeInsets.zero,
                              title: Text(sound.soundTitle),
                              subtitle: sound.artist != null ? Text(sound.artist!) : null,
                              trailing: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  if (sound.isTrending)
                                    const Padding(
                                      padding: EdgeInsets.only(right: 8),
                                      child: Text(
                                        'Trending',
                                        style: TextStyle(color: Colors.orange, fontWeight: FontWeight.bold, fontSize: 12),
                                      ),
                                    ),
                                  TextButton(
                                    onPressed: () => _useSound(sound.id),
                                    child: Text(_selectedSoundId == sound.id ? 'Using' : 'Use'),
                                  ),
                                ],
                              ),
                            )),
                    ],
                  ],
                ),
    );
  }
}
