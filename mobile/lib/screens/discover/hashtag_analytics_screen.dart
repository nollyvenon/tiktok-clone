import 'package:flutter/material.dart';

import '../../services/hashtag_service.dart';

class HashtagAnalyticsScreen extends StatefulWidget {
  final String hashtag;

  const HashtagAnalyticsScreen({super.key, required this.hashtag});

  @override
  State<HashtagAnalyticsScreen> createState() => _HashtagAnalyticsScreenState();
}

class _HashtagAnalyticsScreenState extends State<HashtagAnalyticsScreen> {
  final _hashtagService = HashtagService();
  List<HashtagAnalyticsPoint> _analytics = [];
  Map<String, dynamic>? _stats;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final analytics = await _hashtagService.getAnalytics(widget.hashtag, days: 30);
      final stats = await _hashtagService.getStats(widget.hashtag);
      setState(() {
        _analytics = analytics.reversed.toList();
        _stats = stats;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final maxUsage = _analytics.isEmpty
        ? 1
        : _analytics.map((a) => a.usageCount).reduce((a, b) => a > b ? a : b).clamp(1, 1 << 30);

    return Scaffold(
      appBar: AppBar(title: Text('#${widget.hashtag}')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    if (_stats != null)
                      GridView.count(
                        crossAxisCount: 2,
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        childAspectRatio: 2.2,
                        children: [
                          _StatTile(label: 'Total posts', value: '${_stats!['usage_count'] ?? 0}'),
                          _StatTile(label: 'Creators', value: '${_stats!['unique_creators'] ?? 0}'),
                          _StatTile(label: 'Popularity', value: '${_stats!['popularity_score'] ?? 0}'),
                          _StatTile(
                            label: 'Growth',
                            value: '${(_stats!['trend_velocity'] as num? ?? 0).round()}%',
                          ),
                        ],
                      ),
                    const SizedBox(height: 16),
                    const Text('Usage over the last 30 days', style: TextStyle(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 12),
                    if (_analytics.isEmpty)
                      const Text('No analytics data yet', style: TextStyle(color: Colors.grey))
                    else
                      SizedBox(
                        height: 180,
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: _analytics.map((point) {
                            final heightFraction = point.usageCount / maxUsage;
                            return Expanded(
                              child: Padding(
                                padding: const EdgeInsets.symmetric(horizontal: 1),
                                child: Tooltip(
                                  message: '${point.date.split('T').first}: ${point.usageCount}',
                                  child: FractionallySizedBox(
                                    heightFactor: heightFraction.clamp(0.02, 1.0),
                                    alignment: Alignment.bottomCenter,
                                    child: Container(
                                      decoration: BoxDecoration(
                                        color: Colors.pink,
                                        borderRadius: BorderRadius.circular(2),
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                            );
                          }).toList(),
                        ),
                      ),
                  ],
                ),
    );
  }
}

class _StatTile extends StatelessWidget {
  final String label;
  final String value;

  const _StatTile({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
        Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
      ],
    );
  }
}
