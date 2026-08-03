import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../providers/auth_provider.dart';
import '../auth/two_factor_setup_screen.dart';
import '../notifications/notification_settings_screen.dart';
import 'preferences_screen.dart';
import 'account_settings_screen.dart';
import 'blocked_users_screen.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        children: [
          ListTile(
            leading: const Icon(Icons.person_outline),
            title: const Text('Account'),
            subtitle: const Text('Password, data export, delete account'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const AccountSettingsScreen()),
            ),
          ),
          ListTile(
            leading: const Icon(Icons.notifications_outlined),
            title: const Text('Notifications'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const NotificationSettingsScreen()),
            ),
          ),
          ListTile(
            leading: const Icon(Icons.tune),
            title: const Text('For You Preferences'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const PreferencesScreen()),
            ),
          ),
          ListTile(
            leading: const Icon(Icons.block),
            title: const Text('Blocked Users'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const BlockedUsersScreen()),
            ),
          ),
          ListTile(
            leading: const Icon(Icons.security),
            title: const Text('Two-Factor Authentication'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const TwoFactorSetupScreen()),
            ),
          ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.logout, color: Colors.red),
            title: const Text('Logout', style: TextStyle(color: Colors.red)),
            onTap: () => context.read<AuthProvider>().logout(),
          ),
        ],
      ),
    );
  }
}
