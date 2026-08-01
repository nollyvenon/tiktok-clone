import 'package:flutter/material.dart';

import '../../services/auth_service.dart';

class TwoFactorSetupScreen extends StatefulWidget {
  const TwoFactorSetupScreen({super.key});

  @override
  State<TwoFactorSetupScreen> createState() => _TwoFactorSetupScreenState();
}

class _TwoFactorSetupScreenState extends State<TwoFactorSetupScreen> {
  final _authService = AuthService();
  final _codeController = TextEditingController();
  String? _qrCodeUri;
  bool _isLoading = true;
  bool _isVerifying = false;
  bool _enabled = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadSetup();
  }

  Future<void> _loadSetup() async {
    try {
      final result = await _authService.setup2FA();
      setState(() {
        _qrCodeUri = result['qr_code_uri'] as String?;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _verify() async {
    setState(() {
      _isVerifying = true;
      _error = null;
    });
    try {
      await _authService.verify2FA(_codeController.text.trim());
      setState(() => _enabled = true);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _isVerifying = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Two-factor authentication')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : _enabled
                ? Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.verified_user, size: 64, color: Colors.green),
                      const SizedBox(height: 16),
                      const Text('Two-factor authentication is now enabled.'),
                      const SizedBox(height: 24),
                      ElevatedButton(
                        onPressed: () => Navigator.of(context).pop(),
                        child: const Text('Done'),
                      ),
                    ],
                  )
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      const Text(
                        '1. Scan this into Google Authenticator, Authy, or a similar app',
                      ),
                      const SizedBox(height: 16),
                      if (_qrCodeUri != null)
                        Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            border: Border.all(color: Colors.grey.shade300),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: SelectableText(
                            _qrCodeUri!,
                            style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
                          ),
                        ),
                      const SizedBox(height: 24),
                      const Text('2. Enter the 6-digit code from your app'),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _codeController,
                        keyboardType: TextInputType.number,
                        maxLength: 6,
                        decoration: const InputDecoration(
                          labelText: 'Verification code',
                          border: OutlineInputBorder(),
                          counterText: '',
                        ),
                      ),
                      if (_error != null) ...[
                        const SizedBox(height: 8),
                        Text(_error!, style: TextStyle(color: Colors.red.shade700)),
                      ],
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _isVerifying ? null : _verify,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.pink,
                          foregroundColor: Colors.white,
                        ),
                        child: _isVerifying
                            ? const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                              )
                            : const Text('Enable 2FA'),
                      ),
                    ],
                  ),
      ),
    );
  }
}
