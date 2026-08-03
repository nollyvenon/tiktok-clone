import 'package:flutter/material.dart';

import '../../models/creator_fund.dart';
import '../../services/creator_fund_service.dart';
import '../../services/auth_service.dart';

class CreatorFundScreen extends StatefulWidget {
  const CreatorFundScreen({super.key});

  @override
  State<CreatorFundScreen> createState() => _CreatorFundScreenState();
}

class _CreatorFundScreenState extends State<CreatorFundScreen> {
  final _fundService = CreatorFundService();
  List<FundingProgram> _programs = [];
  List<CreatorApplication> _applications = [];
  bool _isLoading = true;
  String? _error;
  String? _applyingProgramId;

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
        _fundService.listPrograms(),
        _fundService.getMyApplications(),
      ]);
      if (!mounted) return;
      setState(() {
        _programs = results[0] as List<FundingProgram>;
        _applications = results[1] as List<CreatorApplication>;
      });
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _apply(String programId) async {
    setState(() => _applyingProgramId = programId);
    try {
      await _fundService.applyToProgram(programId);
      await _load();
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
      }
    } finally {
      if (mounted) setState(() => _applyingProgramId = null);
    }
  }

  bool _hasApplied(String programId) => _applications.any((a) => a.programId == programId);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Creator Fund')),
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
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text(
          'Apply to funding programs based on your follower count, published videos, and total views.',
          style: TextStyle(color: Colors.grey, fontSize: 13),
        ),
        const SizedBox(height: 16),
        if (_programs.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 24),
            child: Text('No funding programs are open right now.', style: TextStyle(color: Colors.grey)),
          )
        else
          ..._programs.map((program) {
            final applied = _hasApplied(program.id);
            return Container(
              margin: const EdgeInsets.only(bottom: 12),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                border: Border.all(color: Colors.grey.shade300),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(program.name, style: const TextStyle(fontWeight: FontWeight.bold)),
                  if (program.description != null && program.description!.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Text(program.description!, style: const TextStyle(color: Colors.grey)),
                  ],
                  const SizedBox(height: 8),
                  Text(
                    'Requires ${program.minFollowers}+ followers · ${program.minPublishedVideos}+ published videos · ${program.minTotalViews}+ total views',
                    style: const TextStyle(fontSize: 12, color: Colors.grey),
                  ),
                  Text(
                    'Award: \$${(program.awardAmount / 100).toStringAsFixed(2)}',
                    style: const TextStyle(fontSize: 12, color: Colors.grey),
                  ),
                  const SizedBox(height: 8),
                  Align(
                    alignment: Alignment.centerRight,
                    child: applied
                        ? const Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.check_circle, size: 16, color: Colors.green),
                              SizedBox(width: 4),
                              Text('Applied', style: TextStyle(color: Colors.green, fontWeight: FontWeight.bold)),
                            ],
                          )
                        : ElevatedButton(
                            onPressed: _applyingProgramId == program.id ? null : () => _apply(program.id),
                            style: ElevatedButton.styleFrom(backgroundColor: Colors.pink, foregroundColor: Colors.white),
                            child: Text(_applyingProgramId == program.id ? 'Applying...' : 'Apply'),
                          ),
                  ),
                ],
              ),
            );
          }),
        const SizedBox(height: 16),
        const Text('Your Applications', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        if (_applications.isEmpty)
          const Text("You haven't applied to any funding programs yet.", style: TextStyle(color: Colors.grey))
        else
          ..._applications.map((application) {
            final statusColor = application.status == 'approved'
                ? Colors.green
                : application.status == 'rejected'
                    ? Colors.grey
                    : Colors.orange;
            final statusLabel = application.status == 'approved'
                ? 'Approved'
                : application.status == 'rejected'
                    ? 'Not approved'
                    : 'Under review';
            return ListTile(
              contentPadding: EdgeInsets.zero,
              title: Text(
                '${application.followersCount} followers · ${application.publishedVideosCount} videos · ${application.totalViewsCount} views',
              ),
              subtitle: application.status == 'approved'
                  ? Text('Awarded \$${((application.awardedAmount ?? 0) / 100).toStringAsFixed(2)}')
                  : application.decisionReason != null
                      ? Text(application.decisionReason!)
                      : null,
              trailing: Text(statusLabel, style: TextStyle(color: statusColor, fontWeight: FontWeight.bold, fontSize: 12)),
            );
          }),
      ],
    );
  }
}
