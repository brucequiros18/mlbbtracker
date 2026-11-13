import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/config/api_config.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../shared/widgets/app_card.dart';
import '../../../shared/widgets/hero_avatar.dart';
import '../../../shared/widgets/section_header.dart';
import '../../../shared/widgets/state_views.dart';
import '../../../shared/widgets/stat_tile.dart';
import '../../heroes/domain/hero.dart';
import '../../heroes/presentation/hero_providers.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final palette = AppPalette.of(context);
    final rankings = ref.watch(heroRankingsProvider);

    return Scaffold(
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () async => ref.invalidate(heroRankingsProvider),
          child: ListView(
            padding: const EdgeInsets.all(AppSpacing.gutter),
            children: [
              Text('MLBB Tracker', style: Theme.of(context).textTheme.headlineMedium),
              const SizedBox(height: AppSpacing.xs),
              Text(
                'Competitive hero analytics for Mobile Legends: Bang Bang',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: AppSpacing.lg),
              _SearchEntry(onTap: () => context.go('/players')),
              const SizedBox(height: AppSpacing.lg),
              if (ApiConfig.isDev) const _PlayerDataNotice(),
              const SizedBox(height: AppSpacing.lg),
              const SectionHeader(
                title: 'Trending Heroes',
                subtitle: 'Highest win rate · last 7 days · all ranks',
              ),
              rankings.when(
                loading: () => const SizedBox(
                  height: 150,
                  child: LoadingView(),
                ),
                error: (e, _) => ErrorView(
                  message: e.toString(),
                  onRetry: () => ref.invalidate(heroRankingsProvider),
                ),
                data: (stats) {
                  final top = stats.take(5).toList();
                  if (top.isEmpty) {
                    return const EmptyView(
                      icon: Icons.shield_outlined,
                      title: 'No ranking data',
                      message: 'The provider returned no hero statistics.',
                    );
                  }
                  return SizedBox(
                    height: 172,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      itemCount: top.length,
                      separatorBuilder: (_, _) => const SizedBox(width: AppSpacing.md),
                      itemBuilder: (_, i) => _TrendingCard(stat: top[i]),
                    ),
                  );
                },
              ),
              const SizedBox(height: AppSpacing.xl),
              const SectionHeader(title: 'Explore'),
              Row(
                children: [
                  Expanded(
                    child: _ExploreTile(
                      icon: Icons.shield_rounded,
                      title: 'Heroes',
                      subtitle: 'Roster & builds',
                      onTap: () => context.go('/heroes'),
                    ),
                  ),
                  const SizedBox(width: AppSpacing.md),
                  Expanded(
                    child: _ExploreTile(
                      icon: Icons.leaderboard_rounded,
                      title: 'Ranks',
                      subtitle: 'Meta rankings',
                      onTap: () => context.go('/leaderboards'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.lg),
              Container(
                padding: const EdgeInsets.all(AppSpacing.md),
                decoration: BoxDecoration(
                  color: palette.backgroundSecondary,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: palette.border),
                ),
                child: Row(
                  children: [
                    Icon(Icons.schedule_rounded, color: palette.textMuted, size: 18),
                    const SizedBox(width: AppSpacing.sm),
                    Expanded(
                      child: Text(
                        'Hero stats are live from the Rone Arena community API via the MLBB Tracker backend.',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SearchEntry extends StatelessWidget {
  const _SearchEntry({required this.onTap});
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    return AppCard(
      onTap: onTap,
      child: Row(
        children: [
          Icon(Icons.search_rounded, color: palette.accent),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Search a player', style: Theme.of(context).textTheme.titleSmall),
                const SizedBox(height: 2),
                Text('Player ID + Zone ID', style: Theme.of(context).textTheme.bodySmall),
              ],
            ),
          ),
          Icon(Icons.chevron_right_rounded, color: palette.textMuted),
        ],
      ),
    );
  }
}

class _PlayerDataNotice extends StatelessWidget {
  const _PlayerDataNotice();

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    return Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: palette.warning.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: palette.warning.withValues(alpha: 0.4)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.info_outline_rounded, color: palette.warning, size: 20),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Text(
              'Player search is limited: public MLBB sources expose no per-player stats. '
              'Hero and ranking data is real; player profiles need an authenticated source.',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(color: palette.textSecondary),
            ),
          ),
        ],
      ),
    );
  }
}

class _TrendingCard extends StatelessWidget {
  const _TrendingCard({required this.stat});
  final HeroRankStat stat;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 132,
      child: AppCard(
        onTap: () => context.push('/hero/${stat.id}'),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            HeroAvatar(imageUrl: stat.headImage, name: stat.name, size: 44),
            const SizedBox(height: AppSpacing.md),
            Text(
              stat.name,
              style: Theme.of(context).textTheme.titleSmall,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            const Spacer(),
            StatTile(
              label: 'WIN RATE',
              value: formatPercent(stat.winRate),
              valueColor: AppPalette.of(context).positive,
            ),
          ],
        ),
      ),
    );
  }
}

class _ExploreTile extends StatelessWidget {
  const _ExploreTile({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    return AppCard(
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: palette.accent),
          const SizedBox(height: AppSpacing.md),
          Text(title, style: Theme.of(context).textTheme.titleSmall),
          Text(subtitle, style: Theme.of(context).textTheme.bodySmall),
        ],
      ),
    );
  }
}
