import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/theme_providers.dart';
import '../../../shared/widgets/app_card.dart';
import '../../../shared/widgets/hero_avatar.dart';
import '../../../shared/widgets/state_views.dart';
import '../../heroes/presentation/hero_providers.dart';
import 'favorites_providers.dart';

class SavedScreen extends ConsumerWidget {
  const SavedScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final favorites = ref.watch(favoriteHeroesProvider);
    final heroes = ref.watch(allHeroesProvider);
    final mode = ref.watch(themeModeProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Saved'),
        actions: [
          IconButton(
            tooltip: 'Toggle theme',
            icon: Icon(mode == ThemeMode.dark ? Icons.light_mode_rounded : Icons.dark_mode_rounded),
            onPressed: () => ref.read(themeModeProvider.notifier).state =
                mode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark,
          ),
        ],
      ),
      body: heroes.when(
        loading: () => const LoadingView(),
        error: (e, _) => ErrorView(
          message: e.toString(),
          onRetry: () => ref.invalidate(allHeroesProvider),
        ),
        data: (list) {
          final saved = list.where((h) => favorites.contains(h.id)).toList();
          if (saved.isEmpty) {
            return const EmptyView(
              icon: Icons.bookmark_outline_rounded,
              title: 'Nothing saved yet',
              message: 'Open a hero and tap the bookmark icon to keep it here.',
            );
          }
          return ListView.separated(
            padding: const EdgeInsets.all(AppSpacing.gutter),
            itemCount: saved.length,
            separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.sm),
            itemBuilder: (_, i) {
              final hero = saved[i];
              return AppCard(
                padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md, vertical: AppSpacing.md),
                onTap: () => context.push('/hero/${hero.slug.isNotEmpty ? hero.slug : hero.id}'),
                child: Row(
                  children: [
                    HeroAvatar(imageUrl: hero.headImage, name: hero.name, size: 44),
                    const SizedBox(width: AppSpacing.md),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(hero.name, style: Theme.of(context).textTheme.titleSmall),
                          Text(hero.primaryRole, style: Theme.of(context).textTheme.bodySmall),
                        ],
                      ),
                    ),
                    IconButton(
                      onPressed: () => ref.read(favoriteHeroesProvider.notifier).toggle(hero.id),
                      icon: Icon(Icons.bookmark_rounded, color: AppPalette.of(context).accent),
                    ),
                  ],
                ),
              );
            },
          );
        },
      ),
    );
  }
}
