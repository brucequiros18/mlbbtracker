import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../features/heroes/presentation/hero_detail_screen.dart';
import '../../features/heroes/presentation/heroes_screen.dart';
import '../../features/home/presentation/home_screen.dart';
import '../../features/leaderboards/presentation/leaderboards_screen.dart';
import '../../features/players/presentation/player_search_screen.dart';
import '../../features/saved/presentation/saved_screen.dart';
import '../../features/shell/presentation/app_shell.dart';

final _rootKey = GlobalKey<NavigatorState>(debugLabel: 'root');

/// Application router. Five primary destinations live inside a stateful
/// navigation shell; the hero detail screen pushes above it full-screen.
final appRouter = GoRouter(
  navigatorKey: _rootKey,
  initialLocation: '/home',
  routes: [
    StatefulShellRoute.indexedStack(
      builder: (context, state, navigationShell) => AppShell(navigationShell: navigationShell),
      branches: [
        StatefulShellBranch(routes: [
          GoRoute(path: '/home', builder: (_, _) => const HomeScreen()),
        ]),
        StatefulShellBranch(routes: [
          GoRoute(path: '/players', builder: (_, _) => const PlayerSearchScreen()),
        ]),
        StatefulShellBranch(routes: [
          GoRoute(path: '/heroes', builder: (_, _) => const HeroesScreen()),
        ]),
        StatefulShellBranch(routes: [
          GoRoute(path: '/leaderboards', builder: (_, _) => const LeaderboardsScreen()),
        ]),
        StatefulShellBranch(routes: [
          GoRoute(path: '/saved', builder: (_, _) => const SavedScreen()),
        ]),
      ],
    ),
    GoRoute(
      path: '/hero/:identifier',
      builder: (context, state) =>
          HeroDetailScreen(identifier: state.pathParameters['identifier']!),
    ),
  ],
);
