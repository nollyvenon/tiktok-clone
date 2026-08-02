import 'package:flutter/material.dart';

import '../../models/notification.dart';
import '../../services/notification_service.dart';

class NotificationSettingsScreen extends StatefulWidget {
  const NotificationSettingsScreen({super.key});

  @override
  State<NotificationSettingsScreen> createState() => _NotificationSettingsScreenState();
}

class _NotificationSettingsScreenState extends State<NotificationSettingsScreen> {
  final _service = NotificationService();
  NotificationPreferences? _prefs;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final prefs = await _service.getPreferences();
      setState(() => _prefs = prefs);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _update(String key, dynamic value) async {
    try {
      final updated = await _service.updatePreferences({key: value});
      setState(() => _prefs = updated);
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Notification settings')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null || _prefs == null
              ? Center(child: Text(_error ?? 'Failed to load'))
              : ListView(
                  children: [
                    const Padding(
                      padding: EdgeInsets.fromLTRB(16, 16, 16, 8),
                      child: Text('Channels', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey)),
                    ),
                    SwitchListTile(
                      title: const Text('Push notifications'),
                      value: _prefs!.pushEnabled,
                      onChanged: (v) => _update('push_enabled', v),
                    ),
                    SwitchListTile(
                      title: const Text('Email notifications'),
                      value: _prefs!.emailEnabled,
                      onChanged: (v) => _update('email_enabled', v),
                    ),
                    SwitchListTile(
                      title: const Text('In-app notifications'),
                      value: _prefs!.inAppEnabled,
                      onChanged: (v) => _update('in_app_enabled', v),
                    ),
                    const Padding(
                      padding: EdgeInsets.fromLTRB(16, 16, 16, 8),
                      child: Text('Notify me about', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey)),
                    ),
                    SwitchListTile(
                      title: const Text('New followers'),
                      value: _prefs!.followNotifications,
                      onChanged: (v) => _update('follow_notifications', v),
                    ),
                    SwitchListTile(
                      title: const Text('Likes'),
                      value: _prefs!.likeNotifications,
                      onChanged: (v) => _update('like_notifications', v),
                    ),
                    SwitchListTile(
                      title: const Text('Comments'),
                      value: _prefs!.commentNotifications,
                      onChanged: (v) => _update('comment_notifications', v),
                    ),
                    SwitchListTile(
                      title: const Text('Mentions'),
                      value: _prefs!.mentionNotifications,
                      onChanged: (v) => _update('mention_notifications', v),
                    ),
                    SwitchListTile(
                      title: const Text('Direct messages'),
                      value: _prefs!.messageNotifications,
                      onChanged: (v) => _update('message_notifications', v),
                    ),
                    const Padding(
                      padding: EdgeInsets.fromLTRB(16, 16, 16, 8),
                      child: Text('Email digest', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey)),
                    ),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: DropdownButton<String>(
                        value: _prefs!.emailDigestFrequency,
                        isExpanded: true,
                        items: const [
                          DropdownMenuItem(value: 'daily', child: Text('Daily')),
                          DropdownMenuItem(value: 'weekly', child: Text('Weekly')),
                          DropdownMenuItem(value: 'never', child: Text('Never')),
                        ],
                        onChanged: (v) {
                          if (v != null) _update('email_digest_frequency', v);
                        },
                      ),
                    ),
                  ],
                ),
    );
  }
}
