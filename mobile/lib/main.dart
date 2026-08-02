import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import 'providers/auth_provider.dart';
import 'screens/auth/login_screen.dart';
import 'screens/auth/register_screen.dart';
import 'screens/discover/discover_screen.dart';
import 'screens/feed/feed_screen.dart';
import 'screens/foryou/for_you_screen.dart';
import 'screens/profile/profile_screen.dart';
import 'screens/upload/drafts_screen.dart';

void main() {
  runApp(const TikTokCloneApp());
}

class TikTokCloneApp extends StatelessWidget {
  const TikTokCloneApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => AuthProvider()..bootstrap(),
      child: Builder(
        builder: (context) {
          final router = _buildRouter(context.watch<AuthProvider>());
          return MaterialApp.router(
            title: 'TikTok Clone',
            debugShowCheckedModeBanner: false,
            theme: ThemeData(
              colorSchemeSeed: Colors.pink,
              useMaterial3: true,
            ),
            routerConfig: router,
          );
        },
      ),
    );
  }

  GoRouter _buildRouter(AuthProvider authProvider) {
    return GoRouter(
      initialLocation: '/login',
      refreshListenable: authProvider,
      redirect: (context, state) {
        if (authProvider.status == AuthStatus.unknown) return null;

        final isAuthenticated = authProvider.status == AuthStatus.authenticated;
        final isAuthRoute = state.matchedLocation == '/login' || state.matchedLocation == '/register';

        if (!isAuthenticated && !isAuthRoute) return '/login';
        if (isAuthenticated && isAuthRoute) return '/feed';
        return null;
      },
      routes: [
        GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
        GoRoute(path: '/register', builder: (context, state) => const RegisterScreen()),
        GoRoute(
          path: '/feed',
          builder: (context, state) => const MainShell(initialTab: 0),
        ),
        GoRoute(
          path: '/for-you',
          builder: (context, state) => const MainShell(initialTab: 1),
        ),
        GoRoute(
          path: '/discover',
          builder: (context, state) => const MainShell(initialTab: 2),
        ),
        GoRoute(
          path: '/drafts',
          builder: (context, state) => const MainShell(initialTab: 3),
        ),
        GoRoute(
          path: '/profile',
          builder: (context, state) => const MainShell(initialTab: 4),
        ),
      ],
    );
  }
}

/// Bottom-nav shell hosting the feed and the current user's profile.
/// Kept intentionally small - Modules 4+ (upload, messaging, etc.) will
/// add tabs here once they're built out to the same standard as 1-3.
class MainShell extends StatefulWidget {
  final int initialTab;

  const MainShell({super.key, required this.initialTab});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  late int _currentTab = widget.initialTab;

  @override
  Widget build(BuildContext context) {
    final screens = [
      const FeedScreen(),
      const ForYouScreen(),
      const DiscoverScreen(),
      const DraftsScreen(),
      const ProfileScreen(),
    ];

    return Scaffold(
      body: IndexedStack(index: _currentTab, children: screens),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentTab,
        onDestinationSelected: (index) => setState(() => _currentTab = index),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Feed'),
          NavigationDestination(icon: Icon(Icons.auto_awesome_outlined), selectedIcon: Icon(Icons.auto_awesome), label: 'For You'),
          NavigationDestination(icon: Icon(Icons.explore_outlined), selectedIcon: Icon(Icons.explore), label: 'Discover'),
          NavigationDestination(icon: Icon(Icons.video_library_outlined), selectedIcon: Icon(Icons.video_library), label: 'Drafts'),
          NavigationDestination(icon: Icon(Icons.person_outline), selectedIcon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
    );
  }
}
