import 'package:flutter/material.dart';

import '../../models/hashtag_trend.dart';
import '../../services/hashtag_service.dart';
import 'challenge_detail_screen.dart';
import 'hashtag_analytics_screen.dart';

class DiscoverScreen extends StatefulWidget {
  const DiscoverScreen({super.key});

  @override
  State<DiscoverScreen> createState() => _DiscoverScreenState();
}

class _DiscoverScreenState extends State<DiscoverScreen> {
  final _hashtagService = HashtagService();
  List<HashtagTrend> _trends = [];
  List<Challenge> _challenges = [];
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
      final results = await Future.wait([
        _hashtagService.getTrending(),
        _hashtagService.getActiveChallenges(),
      ]);
      setState(() {
        _trends = results[0] as List<HashtagTrend>;
        _challenges = results[1] as List<Challenge>;
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
      appBar: AppBar(title: const Text('Discover')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.emoji_events, color: Colors.amber),
                          SizedBox(width: 8),
                          Text('Active Challenges', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                        ],
                      ),
                      const SizedBox(height: 12),
                      if (_challenges.isEmpty)
                        const Text('No active challenges right now', style: TextStyle(color: Colors.grey))
                      else
                        ..._challenges.map((challenge) => Card(
                              margin: const EdgeInsets.only(bottom: 8),
                              child: ListTile(
                                title: Text('#${challenge.hashtag}'),
                                subtitle: Text(challenge.title),
                                trailing: challenge.prizePool != null
                                    ? Text(
                                        '\$${challenge.prizePool}',
                                        style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.amber),
                                      )
                                    : Text('${challenge.participationCount} entries'),
                                onTap: () => Navigator.of(context).push(
                                  MaterialPageRoute(
                                    builder: (_) => ChallengeDetailScreen(challengeId: challenge.id),
                                  ),
                                ),
                              ),
                            )),
                      const SizedBox(height: 24),
                      const Row(
                        children: [
                          Icon(Icons.trending_up, color: Colors.pink),
                          SizedBox(width: 8),
                          Text('Trending Hashtags', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                        ],
                      ),
                      const SizedBox(height: 12),
                      if (_trends.isEmpty)
                        const Text('No trending hashtags yet', style: TextStyle(color: Colors.grey))
                      else
                        ..._trends.asMap().entries.map((entry) {
                          final index = entry.key;
                          final trend = entry.value;
                          return ListTile(
                            leading: Text('${index + 1}', style: const TextStyle(color: Colors.grey)),
                            title: Text('#${trend.hashtag}'),
                            subtitle: Text('${trend.usageCount} posts · ${trend.uniqueCreators} creators'),
                            trailing: trend.trendVelocity > 0
                                ? Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      const Icon(Icons.local_fire_department, color: Colors.orange, size: 16),
                                      Text(
                                        '${trend.trendVelocity.round()}%',
                                        style: const TextStyle(color: Colors.orange, fontWeight: FontWeight.bold),
                                      ),
                                    ],
                                  )
                                : null,
                            onTap: () => Navigator.of(context).push(
                              MaterialPageRoute(
                                builder: (_) => HashtagAnalyticsScreen(hashtag: trend.hashtag),
                              ),
                            ),
                          );
                        }),
                    ],
                  ),
                ),
    );
  }
}
