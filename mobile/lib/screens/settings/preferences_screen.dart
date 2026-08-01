import 'package:flutter/material.dart';

import '../../services/recommendation_service.dart';

class PreferencesScreen extends StatefulWidget {
  const PreferencesScreen({super.key});

  @override
  State<PreferencesScreen> createState() => _PreferencesScreenState();
}

class _PreferencesScreenState extends State<PreferencesScreen> {
  final _service = RecommendationService();
  final _hashtagsController = TextEditingController();
  double _diversity = 0.5;
  double _recency = 0.5;
  int? _avgWatchTime;
  bool _isLoading = true;
  bool _isSaving = false;
  bool _saved = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final prefs = await _service.getPreferences();
      setState(() {
        _diversity = prefs.contentDiversityScore;
        _recency = prefs.recencyPreference;
        _avgWatchTime = prefs.avgWatchTime;
        _hashtagsController.text = prefs.preferredHashtags.join(', ');
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _save() async {
    setState(() {
      _isSaving = true;
      _saved = false;
      _error = null;
    });
    try {
      await _service.updatePreferences(
        contentDiversityScore: _diversity,
        recencyPreference: _recency,
        preferredHashtags: _hashtagsController.text
            .split(',')
            .map((h) => h.trim())
            .where((h) => h.isNotEmpty)
            .toList(),
      );
      setState(() => _saved = true);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _isSaving = false);
    }
  }

  @override
  void dispose() {
    _hashtagsController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('For You Preferences')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                if (_error != null) ...[
                  Text(_error!, style: TextStyle(color: Colors.red.shade700)),
                  const SizedBox(height: 12),
                ],
                if (_saved) ...[
                  const Row(
                    children: [
                      Icon(Icons.check_circle, color: Colors.green, size: 18),
                      SizedBox(width: 6),
                      Text('Preferences saved'),
                    ],
                  ),
                  const SizedBox(height: 12),
                ],
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Content diversity', style: TextStyle(fontWeight: FontWeight.w600)),
                    Text('${(_diversity * 100).round()}%'),
                  ],
                ),
                Slider(
                  value: _diversity,
                  onChanged: (v) => setState(() => _diversity = v),
                ),
                const Text(
                  'Higher values show a wider mix of creators and topics',
                  style: TextStyle(fontSize: 12, color: Colors.grey),
                ),
                const SizedBox(height: 24),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Prefer recent content', style: TextStyle(fontWeight: FontWeight.w600)),
                    Text('${(_recency * 100).round()}%'),
                  ],
                ),
                Slider(
                  value: _recency,
                  onChanged: (v) => setState(() => _recency = v),
                ),
                const Text(
                  'Higher values prioritize newer videos over older popular ones',
                  style: TextStyle(fontSize: 12, color: Colors.grey),
                ),
                const SizedBox(height: 24),
                TextField(
                  controller: _hashtagsController,
                  decoration: const InputDecoration(
                    labelText: 'Preferred hashtags',
                    hintText: 'dance, comedy, cooking',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 24),
                SizedBox(
                  height: 48,
                  child: ElevatedButton(
                    onPressed: _isSaving ? null : _save,
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.pink, foregroundColor: Colors.white),
                    child: _isSaving
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : const Text('Save preferences'),
                  ),
                ),
                if (_avgWatchTime != null) ...[
                  const SizedBox(height: 24),
                  Center(
                    child: Text(
                      'Average watch time: ${_avgWatchTime}s',
                      style: const TextStyle(fontSize: 12, color: Colors.grey),
                    ),
                  ),
                ],
              ],
            ),
    );
  }
}
