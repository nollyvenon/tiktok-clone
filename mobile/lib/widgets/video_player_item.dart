import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';

import '../models/video.dart';
import '../services/feed_service.dart';

class VideoPlayerItem extends StatefulWidget {
  final Video video;
  final bool isActive;

  const VideoPlayerItem({super.key, required this.video, required this.isActive});

  @override
  State<VideoPlayerItem> createState() => _VideoPlayerItemState();
}

class _VideoPlayerItemState extends State<VideoPlayerItem> {
  VideoPlayerController? _controller;
  final _feedService = FeedService();
  bool _hasTrackedView = false;

  @override
  void initState() {
    super.initState();
    _initializePlayer();
  }

  Future<void> _initializePlayer() async {
    final controller = VideoPlayerController.networkUrl(Uri.parse(widget.video.videoUrl));
    _controller = controller;
    try {
      await controller.initialize();
      controller.setLooping(true);
      if (widget.isActive) {
        controller.play();
      }
      if (mounted) setState(() {});
    } catch (_) {
      // Network/codec failure - the thumbnail fallback in build() covers this
    }
  }

  @override
  void didUpdateWidget(covariant VideoPlayerItem oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isActive && !oldWidget.isActive) {
      _controller?.play();
      if (!_hasTrackedView) {
        _hasTrackedView = true;
        _feedService.trackView(widget.video.id);
      }
    } else if (!widget.isActive && oldWidget.isActive) {
      _controller?.pause();
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  void _togglePlayPause() {
    final controller = _controller;
    if (controller == null || !controller.value.isInitialized) return;
    setState(() {
      controller.value.isPlaying ? controller.pause() : controller.play();
    });
  }

  @override
  Widget build(BuildContext context) {
    final controller = _controller;
    final isReady = controller != null && controller.value.isInitialized;

    return GestureDetector(
      onTap: _togglePlayPause,
      child: Container(
        color: Colors.black,
        child: Stack(
          fit: StackFit.expand,
          children: [
            if (isReady)
              FittedBox(
                fit: BoxFit.cover,
                child: SizedBox(
                  width: controller.value.size.width,
                  height: controller.value.size.height,
                  child: VideoPlayer(controller),
                ),
              )
            else if (widget.video.thumbnailUrl != null)
              Image.network(widget.video.thumbnailUrl!, fit: BoxFit.cover)
            else
              const Center(child: CircularProgressIndicator(color: Colors.white)),
            if (isReady && !controller.value.isPlaying)
              const Center(
                child: Icon(Icons.play_arrow, size: 72, color: Colors.white70),
              ),
          ],
        ),
      ),
    );
  }
}
