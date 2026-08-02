import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:video_player/video_player.dart';

import '../../services/upload_service.dart';

enum _Stage { idle, requestingUrl, uploading, finalizing, creatingDraft, done }

class UploadScreen extends StatefulWidget {
  final String? originalVideoId;
  final String? originalVideoUsername;
  final String? remixType;

  const UploadScreen({
    super.key,
    this.originalVideoId,
    this.originalVideoUsername,
    this.remixType,
  });

  @override
  State<UploadScreen> createState() => _UploadScreenState();
}

class _UploadScreenState extends State<UploadScreen> {
  final _uploadService = UploadService();
  final _titleController = TextEditingController();
  final _descriptionController = TextEditingController();
  File? _videoFile;
  VideoPlayerController? _previewController;
  bool _isPublic = true;
  _Stage _stage = _Stage.idle;
  double _uploadProgress = 0;
  String? _error;

  bool get _isSubmitting => _stage != _Stage.idle && _stage != _Stage.done;

  Future<void> _pickVideo() async {
    final picked = await ImagePicker().pickVideo(source: ImageSource.gallery);
    if (picked == null) return;

    final file = File(picked.path);
    final controller = VideoPlayerController.file(file);
    await controller.initialize();

    setState(() {
      _videoFile = file;
      _previewController?.dispose();
      _previewController = controller;
    });
  }

  Future<void> _submit() async {
    final file = _videoFile;
    if (file == null || _titleController.text.isEmpty) return;

    setState(() {
      _error = null;
      _stage = _Stage.requestingUrl;
    });

    try {
      final filename = file.path.split(Platform.pathSeparator).last;
      final fileSize = await file.length();
      const mimeType = 'video/mp4';

      final presigned = await _uploadService.getPresignedUrl(filename, fileSize, mimeType);
      final uploadId = presigned['upload_id'] as String;
      final presignedUrl = presigned['presigned_url'] as String;

      setState(() => _stage = _Stage.uploading);
      await _uploadService.uploadFile(
        presignedUrl,
        file,
        mimeType,
        onProgress: (p) => setState(() => _uploadProgress = p),
      );

      setState(() => _stage = _Stage.finalizing);
      final duration = _previewController?.value.duration.inSeconds ?? 0;
      await _uploadService.completeUpload(uploadId, presignedUrl, '', duration);

      setState(() => _stage = _Stage.creatingDraft);
      final draft = await _uploadService.createDraft(
        uploadId: uploadId,
        title: _titleController.text,
        description: _descriptionController.text,
        isPublic: _isPublic,
        originalVideoId: widget.originalVideoId,
        remixType: widget.remixType,
      );
      await _uploadService.publishDraft(draft.id);

      setState(() => _stage = _Stage.done);
      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      setState(() {
        _stage = _Stage.idle;
        _uploadProgress = 0;
        _error = e.toString();
      });
    }
  }

  String get _stageLabel {
    switch (_stage) {
      case _Stage.idle:
        return 'Upload';
      case _Stage.requestingUrl:
        return 'Preparing upload...';
      case _Stage.uploading:
        return 'Uploading... ${(_uploadProgress * 100).round()}%';
      case _Stage.finalizing:
        return 'Processing video...';
      case _Stage.creatingDraft:
        return 'Publishing...';
      case _Stage.done:
        return 'Done';
    }
  }

  @override
  void dispose() {
    _previewController?.dispose();
    _titleController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Upload a video')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (widget.originalVideoId != null && widget.remixType != null) ...[
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Icon(widget.remixType == 'duet' ? Icons.repeat : Icons.content_cut, size: 18),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Uploading a ${widget.remixType} response'
                      '${widget.originalVideoUsername != null ? ' to @${widget.originalVideoUsername}' : ''}',
                      style: const TextStyle(fontSize: 13),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
          ],
          if (_error != null) ...[
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.red.shade50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(_error!, style: TextStyle(color: Colors.red.shade700)),
            ),
            const SizedBox(height: 16),
          ],
          GestureDetector(
            onTap: _isSubmitting ? null : _pickVideo,
            child: AspectRatio(
              aspectRatio: 16 / 9,
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.black,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: _previewController != null && _previewController!.value.isInitialized
                    ? ClipRRect(
                        borderRadius: BorderRadius.circular(12),
                        child: FittedBox(
                          fit: BoxFit.cover,
                          child: SizedBox(
                            width: _previewController!.value.size.width,
                            height: _previewController!.value.size.height,
                            child: VideoPlayer(_previewController!),
                          ),
                        ),
                      )
                    : const Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.video_call, color: Colors.white70, size: 48),
                            SizedBox(height: 8),
                            Text('Tap to select a video', style: TextStyle(color: Colors.white70)),
                          ],
                        ),
                      ),
              ),
            ),
          ),
          const SizedBox(height: 24),
          TextField(
            controller: _titleController,
            enabled: !_isSubmitting,
            maxLength: 150,
            onChanged: (_) => setState(() {}),
            decoration: const InputDecoration(labelText: 'Title', border: OutlineInputBorder()),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _descriptionController,
            enabled: !_isSubmitting,
            maxLength: 2200,
            maxLines: 4,
            decoration: const InputDecoration(labelText: 'Description', border: OutlineInputBorder()),
          ),
          const SizedBox(height: 16),
          SwitchListTile(
            title: const Text('Public'),
            subtitle: const Text('Everyone can watch'),
            value: _isPublic,
            onChanged: _isSubmitting ? null : (v) => setState(() => _isPublic = v),
          ),
          const SizedBox(height: 24),
          SizedBox(
            height: 48,
            child: ElevatedButton(
              onPressed: (_videoFile == null || _titleController.text.isEmpty || _isSubmitting)
                  ? null
                  : _submit,
              style: ElevatedButton.styleFrom(backgroundColor: Colors.pink, foregroundColor: Colors.white),
              child: _isSubmitting
                  ? Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        ),
                        const SizedBox(width: 12),
                        Text(_stageLabel),
                      ],
                    )
                  : Text(_stageLabel),
            ),
          ),
        ],
      ),
    );
  }
}
