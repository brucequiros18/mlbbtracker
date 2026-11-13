import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart' show describeError;
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../shared/widgets/app_card.dart';
import '../../../shared/widgets/state_views.dart';
import '../domain/standing.dart';
import 'esports_providers.dart';

const _leagues = <String, String>{
  'id': 'MPL ID',
  'ph': 'MPL PH',
  'my': 'MPL MY',
  'kh': 'MPL KH',
};

class EsportsScreen extends ConsumerWidget {
  const EsportsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final standings = ref.watch(esportsStandingsProvider);
    final league = ref.watch(esportsLeagueProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Esports')),
      body: Column(
        children: [
          SizedBox(
            height: 44,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.gutter),
              itemCount: _leagues.length,
              separatorBuilder: (_, _) => const SizedBox(width: AppSpacing.sm),
              itemBuilder: (context, i) {
                final key = _leagues.keys.elementAt(i);
                return ChoiceChip(
                  label: Text(_leagues[key]!),
                  selected: league == key,
                  onSelected: (_) => ref.read(esportsLeagueProvider.notifier).state = key,
                );
              },
            ),
          ),
          const SizedBox(height: AppSpacing.md),
          Expanded(
            child: standings.when(
              loading: () => const LoadingView(message: 'Loading standings…'),
              error: (e, _) => ErrorView(
                message: describeError(e),
                onRetry: () => ref.invalidate(esportsStandingsProvider),
              ),
              data: (rows) {
                if (rows.isEmpty) {
                  return const EmptyView(
                    icon: Icons.emoji_events_outlined,
                    title: 'No standings',
                    message: 'This league has no published standings yet.',
                  );
                }
                return ListView.separated(
                  padding: const EdgeInsets.fromLTRB(
                      AppSpacing.gutter, 0, AppSpacing.gutter, AppSpacing.xl),
                  itemCount: rows.length,
                  separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.sm),
                  itemBuilder: (_, i) => _StandingRow(row: rows[i]),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _StandingRow extends StatelessWidget {
  const _StandingRow({required this.row});

  final EsportsStanding row;

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    final positive = row.netGameWin >= 0;

    return AppCard(
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md, vertical: AppSpacing.md),
      child: Row(
        children: [
          SizedBox(
            width: 22,
            child: Text(
              '${row.rank}',
              style: Theme.of(context).textTheme.titleSmall?.copyWith(color: palette.textMuted),
            ),
          ),
          _TeamLogo(url: row.logo, code: row.teamCode),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  row.teamCode,
                  style: Theme.of(context).textTheme.titleSmall,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                if (row.teamName != row.teamCode)
                  Text(
                    row.teamName,
                    style: Theme.of(context).textTheme.bodySmall,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
              ],
            ),
          ),
          StatBlock(
            label: 'MP',
            value: '${row.matchPoint}',
          ),
          const SizedBox(width: AppSpacing.lg),
          StatBlock(
            label: 'W-L',
            value: '${row.matchWins}-${row.matchLosses}',
          ),
          const SizedBox(width: AppSpacing.lg),
          StatBlock(
            label: 'NET',
            value: positive ? '+${row.netGameWin}' : '${row.netGameWin}',
            valueColor: positive ? palette.positive : palette.negative,
          ),
        ],
      ),
    );
  }
}

/// Compact numeric block used across standings rows.
class StatBlock extends StatelessWidget {
  const StatBlock({super.key, required this.label, required this.value, this.valueColor});

  final String label;
  final String value;
  final Color? valueColor;

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.end,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          value,
          style: Theme.of(context).textTheme.titleSmall?.copyWith(
                color: valueColor ?? palette.textPrimary,
                fontFeatures: const [FontFeature.tabularFigures()],
              ),
        ),
        Text(label, style: Theme.of(context).textTheme.labelSmall),
      ],
    );
  }
}

class _TeamLogo extends StatelessWidget {
  const _TeamLogo({required this.url, required this.code});

  final String? url;
  final String code;

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    final fallback = Container(
      width: 40,
      height: 40,
      alignment: Alignment.center,
      decoration: BoxDecoration(color: palette.elevated, shape: BoxShape.circle),
      child: Text(
        code.isNotEmpty ? code.characters.first : '?',
        style: Theme.of(context).textTheme.titleSmall,
      ),
    );

    return ClipOval(
      child: SizedBox(
        width: 40,
        height: 40,
        child: (url == null || url!.isEmpty)
            ? fallback
            : CachedNetworkImage(
                imageUrl: url!,
                fit: BoxFit.cover,
                placeholder: (_, _) => Container(width: 40, height: 40, color: palette.elevated),
                errorWidget: (_, _, _) => fallback,
              ),
      ),
    );
  }
}
