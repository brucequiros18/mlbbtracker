import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../shared/widgets/app_card.dart';
import '../../../shared/widgets/hero_avatar.dart';
import '../../../shared/widgets/state_views.dart';
import '../../../shared/widgets/stat_tile.dart';
import '../../heroes/domain/hero.dart';
import '../../heroes/presentation/hero_providers.dart';

const _sorts = {'win_rate': 'Win rate', 'pick_rate': 'Pick rate', 'ban_rate': 'Ban rate'};
const _windows = [1, 3, 7, 15, 30];

class LeaderboardsScreen extends ConsumerWidget {
  const LeaderboardsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final rankings = ref.watch(heroRankingsProvider);
    final sort = ref.watch(rankingSortProvider);
    final days = ref.watch(rankingDaysProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Meta Rankings')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: AppSpacing.gutter),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Wrap(
                  spacing: AppSpacing.sm,
                  children: _sorts.entries
                      .map((e) => ChoiceChip(
                            label: Text(e.value),
                            selected: sort == e.key,
                            onSelected: (_) => ref.read(rankingSortProvider.notifier).state = e.key,
                          ))
                      .toList(),
                ),
                const SizedBox(height: AppSpacing.sm),
                Wrap(
                  spacing: AppSpacing.sm,
                  children: _windows
                      .map((d) => ChoiceChip(
                            label: Text('${d}d'),
                            selected: days == d,
                            onSelected: (_) => ref.read(rankingDaysProvider.notifier).state = d,
                          ))
                      .toList(),
                ),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.md),
          Expanded(
            child: rankings.when(
              loading: () => const LoadingView(message: 'Loading rankings…'),
              error: (e, _) => ErrorView(
                message: e.toString(),
                onRetry: () => ref.invalidate(heroRankingsProvider),
              ),
              data: (list) {
                if (list.isEmpty) {
                  return const EmptyView(
                    icon: Icons.leaderboard_outlined,
                    title: 'No rankings',
                    message: 'No data for this window.',
                  );
                }
                return ListView.separated(
                  padding: const EdgeInsets.fromLTRB(
                      AppSpacing.gutter, 0, AppSpacing.gutter, AppSpacing.xl),
                  itemCount: list.length,
                  separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.sm),
                  itemBuilder: (_, i) => _RankRow(index: i + 1, stat: list[i]),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _RankRow extends StatelessWidget {
  const _RankRow({required this.index, required this.stat});
  final int index;
  final HeroRankStat stat;

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    return AppCard(
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md, vertical: AppSpacing.md),
      onTap: () => context.push('/hero/${stat.id}'),
      child: Row(
        children: [
          SizedBox(
            width: 26,
            child: Text('$index',
                style: Theme.of(context).textTheme.titleSmall?.copyWith(color: palette.textMuted)),
          ),
          HeroAvatar(imageUrl: stat.headImage, name: stat.name, size: 40),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(stat.name, style: Theme.of(context).textTheme.titleSmall),
                if (stat.tier != null)
                  Text('Tier ${stat.tier}', style: Theme.of(context).textTheme.bodySmall),
              ],
            ),
          ),
          StatTile(
            label: 'WIN',
            value: formatPercent(stat.winRate),
            subdued: true,
            valueColor: palette.positive,
            align: CrossAxisAlignment.end,
          ),
          const SizedBox(width: AppSpacing.lg),
          StatTile(
            label: 'PICK',
            value: formatPercent(stat.pickRate, decimals: 1),
            subdued: true,
            align: CrossAxisAlignment.end,
          ),
        ],
      ),
    );
  }
}
