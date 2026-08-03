import 'package:flutter/material.dart';

import '../../models/dashboard.dart';
import '../../services/feed_service.dart';
import '../../services/auth_service.dart';
import '../creator_fund/creator_fund_screen.dart';
import '../collaborations/collaborations_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final _feedService = FeedService();
  CreatorDashboard? _dashboard;
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
      final dashboard = await _feedService.getDashboard(topVideosLimit: 10);
      if (!mounted) return;
      setState(() => _dashboard = dashboard);
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Creator Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.attach_money),
            tooltip: 'Creator Fund',
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const CreatorFundScreen()),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.handshake_outlined),
            tooltip: 'Collaborations',
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const CollaborationsScreen()),
            ),
          ),
        ],
      ),
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
    final dashboard = _dashboard!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(
          'Aggregate performance across all ${dashboard.videoCount} of your videos',
          style: const TextStyle(color: Colors.grey, fontSize: 13),
        ),
        const SizedBox(height: 16),
        GridView.count(
          crossAxisCount: 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          childAspectRatio: 2.2,
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
          children: [
            _StatCard(label: 'Total Views', value: '${dashboard.totalViews}', icon: Icons.visibility),
            _StatCard(label: 'Total Likes', value: '${dashboard.totalLikes}', icon: Icons.favorite),
            _StatCard(label: 'Comments', value: '${dashboard.totalComments}', icon: Icons.comment),
            _StatCard(label: 'Followers', value: '${dashboard.followersCount}', icon: Icons.people),
          ],
        ),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Colors.grey.shade100,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Average engagement rate', style: TextStyle(color: Colors.grey)),
              Text(
                '${dashboard.averageEngagementRate}%',
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
            ],
          ),
        ),
        const SizedBox(height: 24),
        const Text('Top Videos', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        if (dashboard.topVideos.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 24),
            child: Text(
              'No videos yet. Once you publish, your top performers will show up here.',
              style: TextStyle(color: Colors.grey),
            ),
          )
        else
          ...dashboard.topVideos.asMap().entries.map((entry) {
            final index = entry.key;
            final video = entry.value;
            return ListTile(
              contentPadding: EdgeInsets.zero,
              leading: SizedBox(
                width: 32,
                child: Text('${index + 1}', textAlign: TextAlign.center, style: const TextStyle(color: Colors.grey)),
              ),
              title: Text(video.title ?? 'Untitled', maxLines: 1, overflow: TextOverflow.ellipsis),
              subtitle: Text('${video.views} views · ${video.likes} likes · ${video.comments} comments'),
              trailing: Text(
                '${video.engagementRate}%',
                style: const TextStyle(color: Colors.pink, fontWeight: FontWeight.bold),
              ),
            );
          }),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;

  const _StatCard({required this.label, required this.value, required this.icon});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey.shade300),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Row(
            children: [
              Icon(icon, size: 14, color: Colors.grey),
              const SizedBox(width: 6),
              Text(label, style: const TextStyle(color: Colors.grey, fontSize: 12)),
            ],
          ),
          const SizedBox(height: 4),
          Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}
