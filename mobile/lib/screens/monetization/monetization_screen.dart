import 'package:flutter/material.dart';

import '../../models/monetization.dart';
import '../../services/monetization_service.dart';
import '../../services/auth_service.dart';

const _sourceLabels = {
  'creator_fund': 'Creator Fund award',
  'shop_order': 'Shop order',
};

class MonetizationScreen extends StatefulWidget {
  const MonetizationScreen({super.key});

  @override
  State<MonetizationScreen> createState() => _MonetizationScreenState();
}

class _MonetizationScreenState extends State<MonetizationScreen> {
  final _monetizationService = MonetizationService();
  final _payoutController = TextEditingController();

  EarningsSummary? _summary;
  List<Payout> _payouts = [];
  bool _isLoading = true;
  String? _error;
  String? _payoutError;
  bool _isRequesting = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _payoutController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _isLoading = true);
    try {
      final results = await Future.wait([
        _monetizationService.getSummary(),
        _monetizationService.getMyPayouts(),
      ]);
      if (!mounted) return;
      setState(() {
        _summary = results[0] as EarningsSummary;
        _payouts = results[1] as List<Payout>;
      });
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _requestPayout() async {
    setState(() {
      _isRequesting = true;
      _payoutError = null;
    });
    try {
      final amount = ((double.tryParse(_payoutController.text) ?? 0) * 100).round();
      await _monetizationService.requestPayout(amount);
      _payoutController.clear();
      await _load();
    } on ApiException catch (e) {
      setState(() => _payoutError = e.message);
    } finally {
      if (mounted) setState(() => _isRequesting = false);
    }
  }

  String _money(int cents) => '\$${(cents / 100).toStringAsFixed(2)}';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Monetization')),
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
    final summary = _summary!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        GridView.count(
          crossAxisCount: 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          childAspectRatio: 2.2,
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
          children: [
            _StatCard(label: 'Total Earned', value: _money(summary.totalEarned)),
            _StatCard(label: 'Paid Out', value: _money(summary.totalPaidOut)),
            _StatCard(label: 'Pending Payouts', value: _money(summary.pendingPayoutTotal)),
            _StatCard(label: 'Available Balance', value: _money(summary.availableBalance)),
          ],
        ),
        const SizedBox(height: 24),
        const Text('Request a payout', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _payoutController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Amount (\$)', border: OutlineInputBorder()),
              ),
            ),
            const SizedBox(width: 8),
            ElevatedButton(
              onPressed: _isRequesting ? null : _requestPayout,
              child: Text(_isRequesting ? 'Requesting...' : 'Request'),
            ),
          ],
        ),
        if (_payoutError != null) ...[
          const SizedBox(height: 8),
          Text(_payoutError!, style: const TextStyle(color: Colors.red)),
        ],
        const SizedBox(height: 24),
        const Text('Payout requests', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        const SizedBox(height: 8),
        if (_payouts.isEmpty)
          const Text('No payout requests yet.', style: TextStyle(color: Colors.grey))
        else
          ..._payouts.map((payout) => ListTile(
                contentPadding: EdgeInsets.zero,
                title: Text(_money(payout.amount)),
                subtitle: payout.notes != null ? Text(payout.notes!) : null,
                trailing: Text(payout.status, style: const TextStyle(fontWeight: FontWeight.bold)),
              )),
        const SizedBox(height: 24),
        const Text('Earnings history', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        const SizedBox(height: 8),
        if (summary.earnings.isEmpty)
          const Text('No earnings yet.', style: TextStyle(color: Colors.grey))
        else
          ...summary.earnings.map((earning) => ListTile(
                contentPadding: EdgeInsets.zero,
                title: Text(_sourceLabels[earning.sourceType] ?? earning.sourceType),
                trailing: Text('+${_money(earning.amount)}', style: const TextStyle(color: Colors.green, fontWeight: FontWeight.bold)),
              )),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  final String label;
  final String value;

  const _StatCard({required this.label, required this.value});

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
          Text(label, style: const TextStyle(color: Colors.grey, fontSize: 12)),
          const SizedBox(height: 4),
          Text(value, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}
