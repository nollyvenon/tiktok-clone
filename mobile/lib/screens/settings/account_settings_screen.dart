import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../providers/auth_provider.dart';
import '../../services/auth_service.dart';

class AccountSettingsScreen extends StatefulWidget {
  const AccountSettingsScreen({super.key});

  @override
  State<AccountSettingsScreen> createState() => _AccountSettingsScreenState();
}

class _AccountSettingsScreenState extends State<AccountSettingsScreen> {
  final _authService = AuthService();
  final _currentPasswordController = TextEditingController();
  final _newPasswordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _deletePasswordController = TextEditingController();

  bool _isChangingPassword = false;
  String? _passwordError;
  bool _passwordSaved = false;

  bool _isExporting = false;
  bool _showDeleteConfirm = false;
  bool _isDeleting = false;
  String? _deleteError;

  Future<void> _changePassword() async {
    setState(() {
      _isChangingPassword = true;
      _passwordError = null;
      _passwordSaved = false;
    });
    try {
      await _authService.changePassword(
        _currentPasswordController.text,
        _newPasswordController.text,
        _confirmPasswordController.text,
      );
      setState(() => _passwordSaved = true);
      _currentPasswordController.clear();
      _newPasswordController.clear();
      _confirmPasswordController.clear();
    } on ApiException catch (e) {
      setState(() => _passwordError = e.message);
    } finally {
      setState(() => _isChangingPassword = false);
    }
  }

  Future<void> _exportData() async {
    setState(() => _isExporting = true);
    try {
      final data = await _authService.exportMyData();
      if (!mounted) return;
      showDialog(
        context: context,
        builder: (_) => AlertDialog(
          title: const Text('Your data'),
          content: SingleChildScrollView(child: Text(const JsonEncoder.withIndent('  ').convert(data))),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Close')),
          ],
        ),
      );
    } on ApiException catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    } finally {
      if (mounted) setState(() => _isExporting = false);
    }
  }

  Future<void> _deleteAccount() async {
    setState(() {
      _isDeleting = true;
      _deleteError = null;
    });
    try {
      await _authService.deleteAccount(_deletePasswordController.text);
      if (!mounted) return;
      await context.read<AuthProvider>().logout();
    } on ApiException catch (e) {
      setState(() => _deleteError = e.message);
    } finally {
      if (mounted) setState(() => _isDeleting = false);
    }
  }

  @override
  void dispose() {
    _currentPasswordController.dispose();
    _newPasswordController.dispose();
    _confirmPasswordController.dispose();
    _deletePasswordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Account')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('Change password', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 12),
          TextField(
            controller: _currentPasswordController,
            obscureText: true,
            decoration: const InputDecoration(labelText: 'Current password', border: OutlineInputBorder()),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _newPasswordController,
            obscureText: true,
            decoration: const InputDecoration(labelText: 'New password', border: OutlineInputBorder()),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _confirmPasswordController,
            obscureText: true,
            decoration: const InputDecoration(labelText: 'Confirm new password', border: OutlineInputBorder()),
          ),
          if (_passwordError != null) ...[
            const SizedBox(height: 8),
            Text(_passwordError!, style: const TextStyle(color: Colors.red)),
          ],
          if (_passwordSaved) ...[
            const SizedBox(height: 8),
            const Text('Password changed', style: TextStyle(color: Colors.green)),
          ],
          const SizedBox(height: 12),
          ElevatedButton(
            onPressed: _isChangingPassword ? null : _changePassword,
            child: Text(_isChangingPassword ? 'Saving...' : 'Change password'),
          ),
          const SizedBox(height: 32),
          const Text('Export your data', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 8),
          const Text('View a copy of your profile, videos, and comments.', style: TextStyle(color: Colors.grey)),
          const SizedBox(height: 12),
          OutlinedButton(
            onPressed: _isExporting ? null : _exportData,
            child: Text(_isExporting ? 'Preparing...' : 'View my data'),
          ),
          const SizedBox(height: 32),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              border: Border.all(color: Colors.red.shade200),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Delete account', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.red)),
                const SizedBox(height: 4),
                const Text(
                  'This deactivates your account and signs you out everywhere.',
                  style: TextStyle(color: Colors.grey, fontSize: 12),
                ),
                const SizedBox(height: 12),
                if (!_showDeleteConfirm)
                  ElevatedButton(
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.red, foregroundColor: Colors.white),
                    onPressed: () => setState(() => _showDeleteConfirm = true),
                    child: const Text('Delete my account'),
                  )
                else ...[
                  TextField(
                    controller: _deletePasswordController,
                    obscureText: true,
                    decoration: const InputDecoration(
                      labelText: 'Enter your password to confirm',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  if (_deleteError != null) ...[
                    const SizedBox(height: 8),
                    Text(_deleteError!, style: const TextStyle(color: Colors.red)),
                  ],
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      ElevatedButton(
                        style: ElevatedButton.styleFrom(backgroundColor: Colors.red, foregroundColor: Colors.white),
                        onPressed: _isDeleting ? null : _deleteAccount,
                        child: Text(_isDeleting ? 'Deleting...' : 'Confirm deletion'),
                      ),
                      const SizedBox(width: 8),
                      TextButton(
                        onPressed: () => setState(() => _showDeleteConfirm = false),
                        child: const Text('Cancel'),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}
