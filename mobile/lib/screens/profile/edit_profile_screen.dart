import 'package:flutter/material.dart';

import '../../models/user.dart';
import '../../services/profile_service.dart';

class EditProfileScreen extends StatefulWidget {
  final User user;

  const EditProfileScreen({super.key, required this.user});

  @override
  State<EditProfileScreen> createState() => _EditProfileScreenState();
}

class _EditProfileScreenState extends State<EditProfileScreen> {
  final _profileService = ProfileService();
  late final _firstNameController = TextEditingController(text: widget.user.firstName);
  late final _lastNameController = TextEditingController(text: widget.user.lastName);
  late final _bioController = TextEditingController(text: widget.user.bio);
  late final _websiteController = TextEditingController(text: widget.user.website);
  bool _isSaving = false;
  String? _error;

  Future<void> _save() async {
    setState(() {
      _isSaving = true;
      _error = null;
    });
    try {
      await _profileService.updateProfile(
        firstName: _firstNameController.text.trim(),
        lastName: _lastNameController.text.trim(),
        bio: _bioController.text.trim(),
        website: _websiteController.text.trim(),
      );
      if (mounted) Navigator.of(context).pop();
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _isSaving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Edit profile'),
        actions: [
          TextButton(
            onPressed: _isSaving ? null : _save,
            child: _isSaving
                ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                : const Text('Save'),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (_error != null) ...[
            Text(_error!, style: TextStyle(color: Colors.red.shade700)),
            const SizedBox(height: 12),
          ],
          TextField(
            controller: _firstNameController,
            decoration: const InputDecoration(labelText: 'First name', border: OutlineInputBorder()),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _lastNameController,
            decoration: const InputDecoration(labelText: 'Last name', border: OutlineInputBorder()),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _bioController,
            maxLines: 3,
            maxLength: 150,
            decoration: const InputDecoration(labelText: 'Bio', border: OutlineInputBorder()),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _websiteController,
            decoration: const InputDecoration(labelText: 'Website', border: OutlineInputBorder()),
          ),
        ],
      ),
    );
  }
}
