import 'package:flutter/material.dart';

import '../services/moderation_service.dart';
import '../services/auth_service.dart';

const _reasons = [
  {'value': 'spam', 'label': 'Spam'},
  {'value': 'harassment', 'label': 'Harassment or bullying'},
  {'value': 'nudity', 'label': 'Nudity or sexual content'},
  {'value': 'violence', 'label': 'Violence'},
  {'value': 'hate_speech', 'label': 'Hate speech'},
  {'value': 'misinformation', 'label': 'Misinformation'},
  {'value': 'self_harm', 'label': 'Self-harm'},
  {'value': 'other', 'label': 'Other'},
];

class ReportSheet extends StatefulWidget {
  final String contentType;
  final String contentId;

  const ReportSheet({super.key, required this.contentType, required this.contentId});

  static Future<void> show(BuildContext context, {required String contentType, required String contentId}) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (_) => ReportSheet(contentType: contentType, contentId: contentId),
    );
  }

  @override
  State<ReportSheet> createState() => _ReportSheetState();
}

class _ReportSheetState extends State<ReportSheet> {
  final _moderationService = ModerationService();
  final _descriptionController = TextEditingController();
  String _reason = 'spam';
  bool _isSubmitting = false;
  bool _submitted = false;
  String? _error;

  Future<void> _submit() async {
    setState(() {
      _isSubmitting = true;
      _error = null;
    });
    try {
      await _moderationService.createReport(
        contentType: widget.contentType,
        contentId: widget.contentId,
        reason: _reason,
        description: _descriptionController.text,
      );
      setState(() => _submitted = true);
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
      ),
      child: _submitted
          ? const SizedBox(
              height: 120,
              child: Center(
                child: Text(
                  "Thanks - your report has been submitted for review.",
                  textAlign: TextAlign.center,
                ),
              ),
            )
          : Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Report ${widget.contentType}', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                const SizedBox(height: 12),
                RadioGroup<String>(
                  groupValue: _reason,
                  onChanged: (value) => setState(() => _reason = value!),
                  child: Column(
                    children: _reasons
                        .map((r) => RadioListTile<String>(
                              dense: true,
                              contentPadding: EdgeInsets.zero,
                              value: r['value']!,
                              title: Text(r['label']!),
                            ))
                        .toList(),
                  ),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: _descriptionController,
                  maxLines: 3,
                  maxLength: 1000,
                  decoration: const InputDecoration(
                    hintText: 'Additional details (optional)',
                    border: OutlineInputBorder(),
                  ),
                ),
                if (_error != null) ...[
                  const SizedBox(height: 4),
                  Text(_error!, style: const TextStyle(color: Colors.red, fontSize: 12)),
                ],
                const SizedBox(height: 8),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _isSubmitting ? null : _submit,
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.red, foregroundColor: Colors.white),
                    child: _isSubmitting
                        ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                        : const Text('Submit report'),
                  ),
                ),
              ],
            ),
    );
  }
}
