import 'package:flutter/material.dart';

import '../../services/recommendation_service.dart';
import '../profile/profile_screen.dart';

const _algorithmLabels = {
  'collaborative': 'Because people like you watched this',
  'content_based': 'Similar to videos you liked',
  'trending': 'Trending now',
  'social': 'From creators you follow',
};

class ForYouScreen extends StatefulWidget {
  const ForYouScreen({super.key});

  @override
  State<ForYouScreen> createState() => _ForYouScreenState();
}

class _ForYouScreenState extends State<ForYouScreen> {
  final _service = RecommendationService();
  final List<Recommendation> _recommendations = [];
  String? _cursor;
  bool _isLoading = true;
  bool _isLoadingMore = false;
  String? _error;
  final Map<String, String> _feedbackGiven = {};

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final page = await _service.getForYouFeed(limit: 20);
      setState(() {
        _recommendations.addAll(page.recommendations);
        _cursor = page.cursor;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _loadMore() async {
    if (_cursor == null || _isLoadingMore) return;
    setState(() => _isLoadingMore = true);
    try {
      final page = await _service.getForYouFeed(limit: 20, cursor: _cursor);
      setState(() {
        _recommendations.addAll(page.recommendations);
        _cursor = page.cursor;
      });
    } catch (_) {
      // Non-critical: user can retry via pull-to-refresh
    } finally {
      setState(() => _isLoadingMore = false);
    }
  }

  Future<void> _giveFeedback(Recommendation rec, String type) async {
    setState(() => _feedbackGiven[rec.id] = type);
    try {
      await _service.recordFeedback(rec.id, type);
    } catch (_) {
      // Non-critical
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('For You')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : _recommendations.isEmpty
                  ? const Center(
                      child: Padding(
                        padding: EdgeInsets.all(24),
                        child: Text(
                          'No personalized recommendations yet. Watch and like some videos to get started.',
                          textAlign: TextAlign.center,
                        ),
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(12),
                      itemCount: _recommendations.length + (_cursor != null ? 1 : 0),
                      itemBuilder: (context, index) {
                        if (index >= _recommendations.length) {
                          if (!_isLoadingMore) {
                            WidgetsBinding.instance.addPostFrameCallback((_) => _loadMore());
                          }
                          return const Padding(
                            padding: EdgeInsets.all(16),
                            child: Center(child: CircularProgressIndicator()),
                          );
                        }

                        final rec = _recommendations[index];
                        final feedback = _feedbackGiven[rec.id];
                        return Card(
                          margin: const EdgeInsets.only(bottom: 16),
                          clipBehavior: Clip.antiAlias,
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              AspectRatio(
                                aspectRatio: 16 / 9,
                                child: Container(
                                  color: Colors.black,
                                  child: rec.video.thumbnailUrl != null
                                      ? Image.network(rec.video.thumbnailUrl!, fit: BoxFit.cover)
                                      : null,
                                ),
                              ),
                              Padding(
                                padding: const EdgeInsets.all(12),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      _algorithmLabels[rec.algorithm] ?? rec.reason ?? rec.algorithm,
                                      style: const TextStyle(fontSize: 12, color: Colors.grey),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      rec.video.title ?? 'Untitled',
                                      style: const TextStyle(fontWeight: FontWeight.bold),
                                    ),
                                    GestureDetector(
                                      onTap: () => Navigator.of(context).push(
                                        MaterialPageRoute(
                                          builder: (_) => ProfileScreen(userId: rec.video.author.id),
                                        ),
                                      ),
                                      child: Text(
                                        '@${rec.video.author.username}',
                                        style: const TextStyle(color: Colors.grey),
                                      ),
                                    ),
                                    const SizedBox(height: 8),
                                    Row(
                                      children: [
                                        IconButton(
                                          icon: Icon(
                                            Icons.thumb_up,
                                            color: feedback == 'relevant' ? Colors.green : Colors.grey,
                                          ),
                                          onPressed: feedback != null
                                              ? null
                                              : () => _giveFeedback(rec, 'relevant'),
                                        ),
                                        IconButton(
                                          icon: Icon(
                                            Icons.thumb_down,
                                            color: feedback == 'irrelevant' ? Colors.red : Colors.grey,
                                          ),
                                          onPressed: feedback != null
                                              ? null
                                              : () => _giveFeedback(rec, 'irrelevant'),
                                        ),
                                        if (feedback != null)
                                          const Text(
                                            'Thanks for the feedback',
                                            style: TextStyle(fontSize: 12, color: Colors.grey),
                                          ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
    );
  }
}
