import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/network/api_exception.dart' show describeError;
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../shared/widgets/app_card.dart';
import '../../../shared/widgets/hero_avatar.dart';
import '../../../shared/widgets/state_views.dart';
import '../domain/hero.dart';
import 'hero_providers.dart';

const _roles = ['All', 'Tank', 'Fighter', 'Assassin', 'Mage', 'Marksman', 'Support'];

class HeroesScreen extends ConsumerWidget {
  const HeroesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final heroes = ref.watch(heroListProvider);
    final selectedRole = ref.watch(heroRoleFilterProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Heroes')),
      body: Column(
        children: [
          SizedBox(
            height: 44,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.gutter),
              itemCount: _roles.length,
              separatorBuilder: (_, _) => const SizedBox(width: AppSpacing.sm),
              itemBuilder: (context, i) {
                final role = _roles[i];
                return ChoiceChip(
                  label: Text(role),
                  selected: selectedRole == role,
                  onSelected: (_) => ref.read(heroRoleFilterProvider.notifier).state = role,
                );
              },
            ),
          ),
          const SizedBox(height: AppSpacing.md),
          Expanded(
            child: heroes.when(
              loading: () => const LoadingView(message: 'Loading hero roster…'),
              error: (e, _) => ErrorView(
                message: describeError(e),
                onRetry: () => ref.invalidate(heroListProvider),
              ),
              data: (list) {
                if (list.isEmpty) {
                  return const EmptyView(
                    icon: Icons.shield_outlined,
                    title: 'No heroes',
                    message: 'No heroes match this filter.',
                  );
                }
                return GridView.builder(
                  padding: const EdgeInsets.fromLTRB(
                      AppSpacing.gutter, 0, AppSpacing.gutter, AppSpacing.xl),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    mainAxisSpacing: AppSpacing.md,
                    crossAxisSpacing: AppSpacing.md,
                    // Tall enough for avatar + name + role pill without overflow.
                    childAspectRatio: 1.22,
                  ),
                  itemCount: list.length,
                  itemBuilder: (_, i) => _HeroCard(hero: list[i]),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _HeroCard extends StatelessWidget {
  const _HeroCard({required this.hero});
  final HeroSummary hero;

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    return AppCard(
      onTap: () => context.push('/hero/${hero.slug.isNotEmpty ? hero.slug : hero.id}'),
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              HeroAvatar(imageUrl: hero.headImage, name: hero.name, size: 40),
              const Spacer(),
              if (hero.tier != null)
                Text(hero.tier!, style: Theme.of(context).textTheme.titleSmall?.copyWith(color: palette.accent)),
            ],
          ),
          const Spacer(),
          Text(
            hero.name,
            style: Theme.of(context).textTheme.titleSmall,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: AppSpacing.xs),
          Align(
            alignment: Alignment.centerLeft,
            child: RoleTag(label: hero.primaryRole),
          ),
        ],
      ),
    );
  }
}
