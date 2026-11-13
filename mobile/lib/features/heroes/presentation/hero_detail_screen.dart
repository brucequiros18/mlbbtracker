import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../shared/widgets/app_card.dart';
import '../../../shared/widgets/hero_avatar.dart';
import '../../../shared/widgets/section_header.dart';
import '../../../shared/widgets/state_views.dart';
import '../../../shared/widgets/stat_tile.dart';
import '../../saved/presentation/favorites_providers.dart';
import '../domain/hero.dart';
import 'hero_providers.dart';

class HeroDetailScreen extends ConsumerWidget {
  const HeroDetailScreen({super.key, required this.identifier});

  final String identifier;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final detail = ref.watch(heroDetailProvider(identifier));

    return Scaffold(
      appBar: AppBar(title: const Text('Hero')),
      body: detail.when(
        loading: () => const LoadingView(message: 'Loading hero…'),
        error: (e, _) => ErrorView(
          message: e.toString(),
          onRetry: () => ref.invalidate(heroDetailProvider(identifier)),
        ),
        data: (hero) => _HeroDetailBody(hero: hero),
      ),
    );
  }
}

class _HeroDetailBody extends ConsumerWidget {
  const _HeroDetailBody({required this.hero});
  final HeroDetail hero;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final palette = AppPalette.of(context);
    final favorite = ref.watch(favoriteHeroesProvider).contains(hero.id);
    final stat = hero.rankStat;

    return ListView(
      padding: const EdgeInsets.all(AppSpacing.gutter),
      children: [
        AppCard(
          child: Row(
            children: [
              HeroAvatar(imageUrl: hero.portrait ?? hero.headImage, name: hero.name, size: 72),
              const SizedBox(width: AppSpacing.lg),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(hero.name, style: Theme.of(context).textTheme.titleLarge),
                    const SizedBox(height: AppSpacing.sm),
                    Wrap(
                      spacing: AppSpacing.sm,
                      runSpacing: AppSpacing.xs,
                      children: [
                        ...hero.roles.map((r) => RoleTag(label: r)),
                        ...hero.lanes.map((l) => RoleTag(label: l)),
                      ],
                    ),
                  ],
                ),
              ),
              IconButton(
                onPressed: () => ref.read(favoriteHeroesProvider.notifier).toggle(hero.id),
                icon: Icon(
                  favorite ? Icons.bookmark_rounded : Icons.bookmark_outline_rounded,
                  color: favorite ? palette.accent : palette.textMuted,
                ),
              ),
            ],
          ),
        ),
        if (stat != null) ...[
          const SizedBox(height: AppSpacing.lg),
          const SectionHeader(title: 'Ranked Performance', subtitle: 'All ranks · last 7 days'),
          AppCard(
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                StatTile(
                  label: 'WIN RATE',
                  value: formatPercent(stat.winRate),
                  valueColor: palette.positive,
                ),
                StatTile(label: 'PICK RATE', value: formatPercent(stat.pickRate, decimals: 2)),
                StatTile(label: 'BAN RATE', value: formatPercent(stat.banRate, decimals: 2)),
              ],
            ),
          ),
        ],
        if (hero.skills.isNotEmpty) ...[
          const SizedBox(height: AppSpacing.xl),
          const SectionHeader(title: 'Skills'),
          ...hero.skills.map((s) => Padding(
                padding: const EdgeInsets.only(bottom: AppSpacing.md),
                child: AppCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(s.name, style: Theme.of(context).textTheme.titleSmall),
                      const SizedBox(height: AppSpacing.xs),
                      Text(s.description, style: Theme.of(context).textTheme.bodySmall),
                    ],
                  ),
                ),
              )),
        ],
        if (hero.strongAgainst.isNotEmpty || hero.weakAgainst.isNotEmpty) ...[
          const SizedBox(height: AppSpacing.xl),
          const SectionHeader(title: 'Relationships'),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: _RelationList(
                  title: 'Strong with',
                  names: hero.strongAgainst,
                  color: palette.positive,
                ),
              ),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: _RelationList(
                  title: 'Weak against',
                  names: hero.weakAgainst,
                  color: palette.negative,
                ),
              ),
            ],
          ),
        ],
      ],
    );
  }
}

class _RelationList extends StatelessWidget {
  const _RelationList({required this.title, required this.names, required this.color});

  final String title;
  final List<String> names;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: Theme.of(context).textTheme.labelMedium),
          const SizedBox(height: AppSpacing.sm),
          if (names.isEmpty)
            Text('—', style: Theme.of(context).textTheme.bodySmall)
          else
            ...names.map((n) => Padding(
                  padding: const EdgeInsets.only(bottom: 2),
                  child: Row(
                    children: [
                      Container(width: 6, height: 6, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
                      const SizedBox(width: AppSpacing.sm),
                      Expanded(
                        child: Text(n, style: Theme.of(context).textTheme.bodySmall, overflow: TextOverflow.ellipsis),
                      ),
                    ],
                  ),
                )),
        ],
      ),
    );
  }
}
