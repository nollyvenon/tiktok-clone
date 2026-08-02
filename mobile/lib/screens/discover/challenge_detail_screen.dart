import 'package:flutter/material.dart';

import '../../models/hashtag_trend.dart';
import '../../models/video.dart';
import '../../services/hashtag_service.dart';

class ChallengeDetailScreen extends StatefulWidget {
  final String challengeId;

  const ChallengeDetailScreen({super.key, required this.challengeId});

  @override
  State<ChallengeDetailScreen> createState() => _ChallengeDetailScreenState();
}

class _ChallengeDetailScreenState extends State<ChallengeDetailScreen> {
  final _hashtagService = HashtagService();
  Challenge? _challenge;
  List<Video> _videos = [];
  int _total = 0;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final challenge = await _hashtagService.getChallengeDetails(widget.challengeId);
      final (videos, total) = await _hashtagService.getChallengeVideos(widget.challengeId);
      setState(() {
        _challenge = challenge;
        _videos = videos;
        _total = total;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(_challenge != null ? '#${_challenge!.hashtag}' : 'Challenge')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null || _challenge == null
              ? Center(child: Text(_error ?? 'Challenge not found'))
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.emoji_events, color: Colors.amber),
                        const SizedBox(width: 8),
                        Text(
                          _challenge!.title,
                          style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                    if (_challenge!.description != null) ...[
                      const SizedBox(height: 8),
                      Text(_challenge!.description!),
                    ],
                    const SizedBox(height: 16),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('${_challenge!.participationCount} entries'),
                        if (_challenge!.prizePool != null)
                          Text(
                            '\$${_challenge!.prizePool} prize',
                            style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.amber),
                          ),
                        Text(
                          _challenge!.isActive ? 'Active' : 'Ended',
                          style: TextStyle(color: _challenge!.isActive ? Colors.green : Colors.grey),
                        ),
                      ],
                    ),
                    const Divider(height: 32),
                    Text('Entries ($_total)', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 12),
                    if (_videos.isEmpty)
                      const Text('No entries yet — be the first!', style: TextStyle(color: Colors.grey))
                    else
                      GridView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
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
                            child: Container(
                              color: Colors.black12,
                              child: video.thumbnailUrl != null
                                  ? Image.network(video.thumbnailUrl!, fit: BoxFit.cover)
                                  : Center(child: Text(video.title ?? '')),
                            ),
                          );
                        },
                      ),
                  ],
                ),
    );
  }
}
