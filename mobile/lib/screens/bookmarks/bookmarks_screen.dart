import 'package:flutter/material.dart';

import '../../models/video.dart';
import '../../services/feed_service.dart';
import '../../services/auth_service.dart';

class BookmarksScreen extends StatefulWidget {
  const BookmarksScreen({super.key});

  @override
  State<BookmarksScreen> createState() => _BookmarksScreenState();
}

class _BookmarksScreenState extends State<BookmarksScreen> {
  final _feedService = FeedService();
  final List<Video> _videos = [];
  bool _isLoading = true;
  String? _error;

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
      final videos = await _feedService.getBookmarkedVideos(limit: 50);
      setState(() {
        _videos
          ..clear()
          ..addAll(videos);
      });
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _unbookmark(Video video) async {
    try {
      final isBookmarked = await _feedService.toggleBookmark(video.id);
      if (!isBookmarked) {
        setState(() => _videos.removeWhere((v) => v.id == video.id));
      }
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Saved Videos')),
      body: RefreshIndicator(
        onRefresh: _load,
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
                ? Center(child: Text(_error!))
                : _videos.isEmpty
                    ? ListView(
                        children: const [
                          Padding(
                            padding: EdgeInsets.only(top: 120),
                            child: Center(
                              child: Text(
                                "You haven't saved any videos yet.\nTap the bookmark icon on a video to save it here.",
                                textAlign: TextAlign.center,
                                style: TextStyle(color: Colors.grey),
                              ),
                            ),
                          ),
                        ],
                      )
                    : GridView.builder(
                        padding: const EdgeInsets.all(12),
                        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                          crossAxisCount: 2,
                          childAspectRatio: 0.7,
                          crossAxisSpacing: 8,
                          mainAxisSpacing: 8,
                        ),
                        itemCount: _videos.length,
                        itemBuilder: (context, index) {
                          final video = _videos[index];
                          return ClipRRect(
                            borderRadius: BorderRadius.circular(8),
                            child: Stack(
                              fit: StackFit.expand,
                              children: [
                                Container(
                                  color: Colors.black12,
                                  child: video.thumbnailUrl != null
                                      ? Image.network(video.thumbnailUrl!, fit: BoxFit.cover)
                                      : Center(
                                          child: Padding(
                                            padding: const EdgeInsets.all(8),
                                            child: Text(
                                              video.title ?? '',
                                              textAlign: TextAlign.center,
                                              style: const TextStyle(color: Colors.white70),
                                            ),
                                          ),
                                        ),
                                ),
                                Positioned(
                                  top: 4,
                                  right: 4,
                                  child: GestureDetector(
                                    onTap: () => _unbookmark(video),
                                    child: Container(
                                      padding: const EdgeInsets.all(6),
                                      decoration: const BoxDecoration(
                                        color: Colors.black54,
                                        shape: BoxShape.circle,
                                      ),
                                      child: const Icon(Icons.bookmark, color: Colors.white, size: 18),
                                    ),
                                  ),
                                ),
                                Positioned(
                                  left: 6,
                                  right: 6,
                                  bottom: 6,
                                  child: Text(
                                    '@${video.author.username}',
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontSize: 12,
                                      fontWeight: FontWeight.w600,
                                      shadows: [Shadow(color: Colors.black, blurRadius: 4)],
                                    ),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                              ],
                            ),
                          );
                        },
                      ),
      ),
    );
  }
}
