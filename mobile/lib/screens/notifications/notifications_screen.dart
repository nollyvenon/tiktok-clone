import 'package:flutter/material.dart';

import '../../models/notification.dart';
import '../../services/notification_service.dart';
import 'notification_settings_screen.dart';

const _typeIcons = {
  'follow': Icons.person_add,
  'like': Icons.favorite,
  'comment': Icons.comment,
  'mention': Icons.alternate_email,
  'message': Icons.message,
};

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  final _service = NotificationService();
  List<AppNotification> _notifications = [];
  int _unreadCount = 0;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final page = await _service.getNotifications(limit: 50);
      setState(() {
        _notifications = page.notifications;
        _unreadCount = page.unreadCount;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _markRead(AppNotification notification) async {
    try {
      await _service.markAsRead(notification.id);
      setState(() {
        notification.isRead = true;
        _unreadCount = (_unreadCount - 1).clamp(0, 1 << 30);
      });
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
    }
  }

  Future<void> _markAllRead() async {
    try {
      await _service.markAllAsRead();
      setState(() {
        for (final n in _notifications) {
          n.isRead = true;
        }
        _unreadCount = 0;
      });
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
    }
  }

  Future<void> _delete(AppNotification notification) async {
    try {
      await _service.deleteNotification(notification.id);
      setState(() => _notifications.remove(notification));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifications'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const NotificationSettingsScreen()),
            ),
          ),
          if (_unreadCount > 0)
            TextButton(
              onPressed: _markAllRead,
              child: const Text('Mark all read'),
            ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : _notifications.isEmpty
                  ? const Center(child: Text('No notifications yet'))
                  : RefreshIndicator(
                      onRefresh: _load,
                      child: ListView.builder(
                        itemCount: _notifications.length,
                        itemBuilder: (context, index) {
                          final notification = _notifications[index];
                          return Dismissible(
                            key: ValueKey(notification.id),
                            direction: DismissDirection.endToStart,
                            background: Container(
                              color: Colors.red,
                              alignment: Alignment.centerRight,
                              padding: const EdgeInsets.only(right: 20),
                              child: const Icon(Icons.delete, color: Colors.white),
                            ),
                            onDismissed: (_) => _delete(notification),
                            child: Container(
                              color: notification.isRead ? null : Colors.pink.withValues(alpha: 0.05),
                              child: ListTile(
                                leading: CircleAvatar(
                                  child: Icon(_typeIcons[notification.type] ?? Icons.notifications),
                                ),
                                title: Text(notification.title),
                                subtitle: Text(
                                  notification.message ?? _formatTime(notification.createdAt),
                                ),
                                onTap: () => _markRead(notification),
                              ),
                            ),
                          );
                        },
                      ),
                    ),
    );
  }

  String _formatTime(DateTime time) {
    final diff = DateTime.now().difference(time);
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    return '${diff.inDays}d ago';
  }
}
