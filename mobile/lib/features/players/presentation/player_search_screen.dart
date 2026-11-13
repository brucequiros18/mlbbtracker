import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../shared/widgets/app_button.dart';
import '../../../shared/widgets/app_card.dart';
import '../../../shared/widgets/app_text_field.dart';
import '../../../shared/widgets/section_header.dart';
import '../../../shared/widgets/state_views.dart';
import '../domain/player.dart';
import 'player_providers.dart';

class PlayerSearchScreen extends ConsumerStatefulWidget {
  const PlayerSearchScreen({super.key});

  @override
  ConsumerState<PlayerSearchScreen> createState() => _PlayerSearchScreenState();
}

class _PlayerSearchScreenState extends ConsumerState<PlayerSearchScreen> {
  final _playerId = TextEditingController();
  final _zoneId = TextEditingController();
  String? _playerError;
  String? _zoneError;

  @override
  void dispose() {
    _playerId.dispose();
    _zoneId.dispose();
    super.dispose();
  }

  void _submit() {
    final pid = _playerId.text.trim();
    final zid = _zoneId.text.trim();
    setState(() {
      _playerError = pid.isEmpty ? 'Player ID is required' : null;
      _zoneError = zid.isEmpty ? 'Zone ID is required' : null;
    });
    if (pid.isEmpty || zid.isEmpty) return;
    FocusScope.of(context).unfocus();
    ref.read(playerSearchControllerProvider.notifier).search(pid, zid);
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(playerSearchControllerProvider);
    final recent = ref.watch(recentSearchesProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Players')),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.gutter),
        children: [
          Text('Look up a player', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: AppSpacing.xs),
          Text(
            'Enter the Player ID and Zone ID shown in the player’s in-game profile.',
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(height: AppSpacing.lg),
          AppTextField(
            label: 'Player ID',
            hint: 'e.g. 123456789',
            controller: _playerId,
            digitsOnly: true,
            keyboardType: TextInputType.number,
            error: _playerError,
          ),
          const SizedBox(height: AppSpacing.md),
          AppTextField(
            label: 'Zone ID',
            hint: 'e.g. 1234',
            controller: _zoneId,
            digitsOnly: true,
            keyboardType: TextInputType.number,
            error: _zoneError,
            onSubmitted: (_) => _submit(),
          ),
          const SizedBox(height: AppSpacing.lg),
          AppPrimaryButton(
            label: 'Search',
            icon: Icons.search_rounded,
            loading: state is PlayerSearchLoading,
            onPressed: _submit,
          ),
          const SizedBox(height: AppSpacing.xl),
          switch (state) {
            PlayerSearchIdle() => _RecentList(recent: recent, onTap: (r) {
                _playerId.text = r.playerId;
                _zoneId.text = r.zoneId;
                _submit();
              }),
            PlayerSearchLoading() => const SizedBox.shrink(),
            PlayerSearchSuccess(:final profile) => _ProfileCard(profile: profile),
            PlayerSearchUnavailable(:final message) => _UnavailableCard(message: message),
            PlayerSearchFailure(:final message) => ErrorView(message: message, onRetry: _submit),
          },
        ],
      ),
    );
  }
}

class _RecentList extends ConsumerWidget {
  const _RecentList({required this.recent, required this.onTap});
  final List<RecentSearch> recent;
  final ValueChanged<RecentSearch> onTap;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (recent.isEmpty) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SectionHeader(
          title: 'Recent searches',
          trailing: TextButton(
            onPressed: () => ref.read(recentSearchesProvider.notifier).clear(),
            child: const Text('Clear'),
          ),
        ),
        ...recent.map((r) => Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.sm),
              child: AppCard(
                padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md, vertical: AppSpacing.md),
                onTap: () => onTap(r),
                child: Row(
                  children: [
                    Icon(Icons.history_rounded, color: AppPalette.of(context).textMuted, size: 18),
                    const SizedBox(width: AppSpacing.md),
                    Expanded(child: Text(r.label, style: Theme.of(context).textTheme.bodyMedium)),
                    Icon(Icons.north_west_rounded, color: AppPalette.of(context).textMuted, size: 16),
                  ],
                ),
              ),
            )),
      ],
    );
  }
}

class _UnavailableCard extends StatelessWidget {
  const _UnavailableCard({required this.message});
  final String message;

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    return AppCard(
      borderColor: palette.warning.withValues(alpha: 0.5),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.lock_outline_rounded, color: palette.warning, size: 20),
              const SizedBox(width: AppSpacing.sm),
              Text('Not available from public data', style: Theme.of(context).textTheme.titleSmall),
            ],
          ),
          const SizedBox(height: AppSpacing.sm),
          Text(message, style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: AppSpacing.sm),
          Text(
            'MLBB Tracker shows real hero and meta data. Per-player statistics currently require '
            'an authenticated source, so this screen never displays fabricated numbers.',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(color: palette.textMuted),
          ),
        ],
      ),
    );
  }
}

class _ProfileCard extends StatelessWidget {
  const _ProfileCard({required this.profile});
  final PlayerProfile profile;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(profile.ign, style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: AppSpacing.xs),
          Text('ID ${profile.playerId} · Zone ${profile.zoneId}',
              style: Theme.of(context).textTheme.bodySmall),
          if (profile.rankName != null) ...[
            const SizedBox(height: AppSpacing.sm),
            Text('Rank: ${profile.rankName}', style: Theme.of(context).textTheme.bodyMedium),
          ],
        ],
      ),
    );
  }
}
