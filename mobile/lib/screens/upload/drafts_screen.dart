import 'package:flutter/material.dart';

import '../../models/draft.dart';
import '../../services/upload_service.dart';
import 'upload_screen.dart';

class DraftsScreen extends StatefulWidget {
  const DraftsScreen({super.key});

  @override
  State<DraftsScreen> createState() => _DraftsScreenState();
}

class _DraftsScreenState extends State<DraftsScreen> {
  final _uploadService = UploadService();
  List<Draft> _drafts = [];
  bool _isLoading = true;
  String? _error;
  String? _actioningId;

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
      final drafts = await _uploadService.getUserDrafts();
      setState(() => _drafts = drafts);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _publish(String id) async {
    setState(() => _actioningId = id);
    try {
      await _uploadService.publishDraft(id);
      setState(() => _drafts.removeWhere((d) => d.id == id));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
    } finally {
      setState(() => _actioningId = null);
    }
  }

  Future<void> _delete(String id) async {
    setState(() => _actioningId = id);
    try {
      await _uploadService.deleteDraft(id);
      setState(() => _drafts.removeWhere((d) => d.id == id));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
    } finally {
      setState(() => _actioningId = null);
    }
  }

  Future<void> _schedule(String id) async {
    final now = DateTime.now();
    final date = await showDatePicker(
      context: context,
      initialDate: now.add(const Duration(days: 1)),
      firstDate: now,
      lastDate: now.add(const Duration(days: 365)),
    );
    if (date == null || !mounted) return;
    final time = await showTimePicker(context: context, initialTime: TimeOfDay.now());
    if (time == null) return;

    final publishAt = DateTime(date.year, date.month, date.day, time.hour, time.minute);
    setState(() => _actioningId = id);
    try {
      await _uploadService.scheduleDraft(id, publishAt);
      await _load();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
    } finally {
      setState(() => _actioningId = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Your drafts'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: () async {
              final published = await Navigator.of(context).push<bool>(
                MaterialPageRoute(builder: (_) => const UploadScreen()),
              );
              if (published == true) _load();
            },
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : _drafts.isEmpty
                  ? const Center(child: Text('No drafts yet'))
                  : RefreshIndicator(
                      onRefresh: _load,
                      child: ListView.builder(
                        itemCount: _drafts.length,
                        itemBuilder: (context, index) {
                          final draft = _drafts[index];
                          final isActioning = _actioningId == draft.id;
                          return ListTile(
                            title: Text(draft.title ?? 'Untitled draft'),
                            subtitle: Text(
                              'Status: ${draft.status}'
                              '${draft.scheduledPublishAt != null ? ' · Scheduled ${draft.scheduledPublishAt}' : ''}',
                            ),
                            trailing: isActioning
                                ? const SizedBox(
                                    width: 20,
                                    height: 20,
                                    child: CircularProgressIndicator(strokeWidth: 2),
                                  )
                                : Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      IconButton(
                                        icon: const Icon(Icons.schedule),
                                        onPressed: () => _schedule(draft.id),
                                      ),
                                      IconButton(
                                        icon: const Icon(Icons.send),
                                        onPressed: () => _publish(draft.id),
                                      ),
                                      IconButton(
                                        icon: const Icon(Icons.delete, color: Colors.red),
                                        onPressed: () => _delete(draft.id),
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
