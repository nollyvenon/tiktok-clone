import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:tiktok_clone/providers/auth_provider.dart';
import 'package:tiktok_clone/screens/auth/login_screen.dart';

void main() {
  testWidgets('LoginScreen shows validation errors on empty submit', (WidgetTester tester) async {
    await tester.pumpWidget(
      ChangeNotifierProvider(
        create: (_) => AuthProvider(),
        child: const MaterialApp(home: LoginScreen()),
      ),
    );

    await tester.tap(find.text('Log in'));
    await tester.pump();

    expect(find.text('Email is required'), findsOneWidget);
    expect(find.text('Password is required'), findsOneWidget);
  });

  testWidgets('LoginScreen rejects an email without @', (WidgetTester tester) async {
    await tester.pumpWidget(
      ChangeNotifierProvider(
        create: (_) => AuthProvider(),
        child: const MaterialApp(home: LoginScreen()),
      ),
    );

    await tester.enterText(find.widgetWithText(TextFormField, 'Email'), 'not-an-email');
    await tester.enterText(find.widgetWithText(TextFormField, 'Password'), 'somepassword');
    await tester.tap(find.text('Log in'));
    await tester.pump();

    expect(find.text('Enter a valid email'), findsOneWidget);
  });
}
