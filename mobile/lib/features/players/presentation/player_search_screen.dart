import 'dart:async';

import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart' show ApiException, ApiErrorKind, describeError;
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../shared/widgets/app_button.dart';
import '../../../shared/widgets/app_card.dart';
import '../../../shared/widgets/app_text_field.dart';
import '../../../shared/widgets/section_header.dart';
import '../../../shared/widgets/state_views.dart';
import '../domain/player.dart';
import 'player_providers.dart';

/// Players tab.
///
/// Shows the **consented connect flow**: the player signs in as themselves
/// with a one-time code delivered to their in-game mailbox. Once connected,
/// the screen renders the player's real statistics, matches and top heroes.
class PlayerSearchScreen extends ConsumerWidget {
  const PlayerSearchScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final token = ref.watch(sessionTokenProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Players'),
        actions: [
          if (token != null)
            IconButton(
              tooltip: 'Disconnect account',
              icon: const Icon(Icons.logout_rounded),
              onPressed: () => _confirmDisconnect(context, ref),
            ),
        ],
      ),
      body: token == null
          ? const _ConnectView()
          : const _ConnectedDashboard(),
    );
  }

  Future<void> _confirmDisconnect(BuildContext context, WidgetRef ref) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Disconnect account?'),
        content: const Text(
          'Your statistics will be removed from this device and the backend '
          'will forget the session. You can reconnect at any time.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Disconnect')),
        ],
      ),
    );
    if (confirmed == true) {
      await ref.read(connectControllerProvider.notifier).disconnect();
    }
  }
}

// — Connect flow —————————————————————————————————————————————
class _ConnectView extends ConsumerStatefulWidget {
  const _ConnectView();

  @override
  ConsumerState<_ConnectView> createState() => _ConnectViewState();
}

class _ConnectViewState extends ConsumerState<_ConnectView> {
  final _playerId = TextEditingController();
  final _zoneId = TextEditingController();
  final _code = TextEditingController();
  String? _playerError;
  String? _zoneError;
  String? _codeError;

  @override
  void dispose() {
    _playerId.dispose();
    _zoneId.dispose();
    _code.dispose();
    super.dispose();
  }

  bool _validateIds() {
    final pid = _playerId.text.trim();
    final zid = _zoneId.text.trim();
    setState(() {
      _playerError = pid.isEmpty ? 'Player ID is required' : null;
      _zoneError = zid.isEmpty ? 'Zone ID is required' : null;
    });
    return pid.isNotEmpty && zid.isNotEmpty;
  }

  void _sendCode() {
    if (!_validateIds()) return;
    FocusScope.of(context).unfocus();
    ref.read(connectControllerProvider.notifier).sendCode(
          _playerId.text.trim(),
          _zoneId.text.trim(),
        );
  }

  void _verify() {
    final code = _code.text.trim();
    setState(() => _codeError = code.length < 4 ? 'Enter the code from your in-game mailbox' : null);
    if (code.length < 4) return;
    FocusScope.of(context).unfocus();
    ref.read(connectControllerProvider.notifier).verify(
          _playerId.text.trim(),
          _zoneId.text.trim(),
          code,
        );
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(connectControllerProvider);
    final palette = AppPalette.of(context);
    final codeSent = state is ConnectCodeSent;
    final busy = state is ConnectSendingCode || state is ConnectVerifying;

    return ListView(
      padding: const EdgeInsets.all(AppSpacing.gutter),
      children: [
        Text('Connect your account', style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: AppSpacing.xs),
        Text(
          'Real match history, KDA and win rates — read directly from your own account.',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        const SizedBox(height: AppSpacing.lg),
        AppCard(
          borderColor: palette.accent.withValues(alpha: 0.45),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(Icons.verified_user_outlined, color: palette.accent, size: 20),
                  const SizedBox(width: AppSpacing.sm),
                  Text('How sign-in works', style: Theme.of(context).textTheme.titleSmall),
                ],
              ),
              const SizedBox(height: AppSpacing.sm),
              _Step(number: '1', text: 'Enter the Player ID and Zone ID from your in-game profile.'),
              _Step(number: '2', text: 'A one-time code is sent to your in-game mailbox.'),
              _Step(number: '3', text: 'Enter the code here. The backend reads your stats for you.'),
              const SizedBox(height: AppSpacing.sm),
              Text(
                'No password is ever requested. Your account token is stored on the '
                'backend, never in the app.',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(color: palette.textMuted),
              ),
            ],
          ),
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
        ),
        const SizedBox(height: AppSpacing.lg),
        if (!codeSent)
          AppPrimaryButton(
            label: 'Send verification code',
            icon: Icons.mark_email_unread_outlined,
            loading: state is ConnectSendingCode,
            onPressed: busy ? null : _sendCode,
          ),
        if (codeSent) ...[
          AppTextField(
            label: 'Verification code',
            hint: 'Code from your in-game mailbox',
            controller: _code,
            digitsOnly: true,
            keyboardType: TextInputType.number,
            maxLength: 8,
            error: _codeError,
            onSubmitted: (_) => _verify(),
          ),
          const SizedBox(height: AppSpacing.md),
          AppPrimaryButton(
            label: 'Connect account',
            icon: Icons.link_rounded,
            loading: state is ConnectVerifying,
            onPressed: busy ? null : _verify,
          ),
          const SizedBox(height: AppSpacing.sm),
          TextButton(
            onPressed: busy ? null : _sendCode,
            child: const Text('Send a new code'),
          ),
        ],
        if (state is ConnectError) ...[
          const SizedBox(height: AppSpacing.md),
          ErrorView(message: state.message, onRetry: codeSent ? _verify : _sendCode),
        ],
        const SizedBox(height: AppSpacing.xl),
        Text(
          'Anonymous lookups of other players are not supported: no public API exposes '
          'another player\'s statistics. This app never fabricates player data.',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(color: palette.textMuted),
        ),
      ],
    );
  }
}

class _Step extends StatelessWidget {
  const _Step({required this.number, required this.text});
  final String number;
  final String text;

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 20,
            height: 20,
            alignment: Alignment.center,
            decoration: BoxDecoration(color: palette.accentSoft, shape: BoxShape.circle),
            child: Text(number, style: Theme.of(context).textTheme.labelSmall?.copyWith(color: palette.accent)),
          ),
          const SizedBox(width: AppSpacing.sm),
          Expanded(child: Text(text, style: Theme.of(context).textTheme.bodySmall)),
        ],
      ),
    );
  }
}

// — Connected dashboard ——————————————————————————————————————
class _ConnectedDashboard extends ConsumerStatefulWidget {
  const _ConnectedDashboard();

  @override
  ConsumerState<_ConnectedDashboard> createState() => _ConnectedDashboardState();
}

class _ConnectedDashboardState extends ConsumerState<_ConnectedDashboard> {
  /// Live tracking: the provider refreshes the player's data continuously, so
  /// the dashboard re-polls while it is open. A completed game shows up here
  /// within a minute.
  static const _pollInterval = Duration(seconds: 60);
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(_pollInterval, (_) => _refresh(silent: true));
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _refresh({bool silent = false}) async {
    ref.invalidate(connectedProfileProvider);
    ref.invalidate(playerStatsProvider);
    ref.invalidate(playerMatchesProvider);
    ref.invalidate(playerHeroesProvider);
    if (silent) return;
    try {
      await Future.wait([
        ref.read(connectedProfileProvider.future),
        ref.read(playerStatsProvider.future),
        ref.read(playerMatchesProvider.future),
        ref.read(playerHeroesProvider.future),
      ]);
    } catch (_) {
      // Errors are surfaced by each section's own error view.
    }
  }

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    final profile = ref.watch(connectedProfileProvider);
    final stats = ref.watch(playerStatsProvider);
    final matches = ref.watch(playerMatchesProvider);
    final heroes = ref.watch(playerHeroesProvider);

    return RefreshIndicator(
      onRefresh: _refresh,
      child: ListView(
        padding: const EdgeInsets.all(AppSpacing.gutter),
        children: [
          profile.when(
            loading: () => const AppCard(
              child: SizedBox(height: 96, child: Center(child: CircularProgressIndicator())),
            ),
            error: (e, _) => _SessionError(error: e),
            data: (p) => _ProfileCard(profile: p),
          ),
          const SizedBox(height: AppSpacing.lg),
          stats.when(
            loading: () => const SizedBox.shrink(),
            error: (e, _) => ErrorView(message: describeError(e), onRetry: () => ref.invalidate(playerStatsProvider)),
            data: (s) => _StatsGrid(stats: s),
          ),
          const SizedBox(height: AppSpacing.sm),
          Row(
            children: [
              Icon(Icons.circle, size: 8, color: palette.positive),
              const SizedBox(width: AppSpacing.xs),
              Text(
                'Live tracking · refreshes every 60s',
                style: Theme.of(context).textTheme.labelSmall?.copyWith(color: palette.textMuted),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.lg),
          SectionHeader(
            title: 'Recent matches',
            subtitle: matches.valueOrNull?.hasNext == true ? 'Showing latest 20' : null,
          ),
          matches.when(
            loading: () => const Padding(
              padding: EdgeInsets.symmetric(vertical: AppSpacing.lg),
              child: Center(child: CircularProgressIndicator()),
            ),
            error: (e, _) => ErrorView(message: describeError(e), onRetry: () => ref.invalidate(playerMatchesProvider)),
            data: (page) => page.matches.isEmpty
                ? const EmptyView(
                    icon: Icons.sports_esports_outlined,
                    title: 'No matches yet',
                    message: 'Matches appear here once your account has played games.',
                  )
                : Column(
                    children: [
                      for (final m in page.matches)
                        Padding(
                          padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                          child: _MatchTile(match: m),
                        ),
                    ],
                  ),
          ),
          const SizedBox(height: AppSpacing.lg),
          SectionHeader(title: 'Top heroes', subtitle: 'By matches played'),
          heroes.when(
            loading: () => const SizedBox.shrink(),
            error: (e, _) => ErrorView(message: describeError(e), onRetry: () => ref.invalidate(playerHeroesProvider)),
            data: (list) => list.isEmpty
                ? const SizedBox.shrink()
                : SizedBox(
                    height: 116,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      itemCount: list.length,
                      separatorBuilder: (_, _) => const SizedBox(width: AppSpacing.sm),
                      itemBuilder: (_, i) => _HeroChip(hero: list[i]),
                    ),
                  ),
          ),
          const SizedBox(height: AppSpacing.xl),
        ],
      ),
    );
  }
}

class _SessionError extends ConsumerWidget {
  const _SessionError({required this.error});
  final Object error;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final expired = error is ApiException && (error as ApiException).kind == ApiErrorKind.unauthorized;
    final palette = AppPalette.of(context);
    return AppCard(
      borderColor: palette.warning.withValues(alpha: 0.5),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            expired ? 'Session expired' : 'Could not load your profile',
            style: Theme.of(context).textTheme.titleSmall,
          ),
          const SizedBox(height: AppSpacing.sm),
          Text(describeError(error), style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: AppSpacing.md),
          AppPrimaryButton(
            label: expired ? 'Reconnect' : 'Retry',
            expand: false,
            onPressed: () => expired
                ? ref.read(connectControllerProvider.notifier).disconnect()
                : ref.invalidate(connectedProfileProvider),
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
    final palette = AppPalette.of(context);
    return AppCard(
      elevated: true,
      child: Row(
        children: [
          ClipOval(
            child: SizedBox(
              width: 56,
              height: 56,
              child: profile.avatar == null || profile.avatar!.isEmpty
                  ? Container(
                      color: palette.elevated,
                      alignment: Alignment.center,
                      child: Icon(Icons.person_rounded, color: palette.textMuted),
                    )
                  : CachedNetworkImage(
                      imageUrl: profile.avatar!,
                      fit: BoxFit.cover,
                      placeholder: (_, _) => Container(color: palette.elevated),
                      errorWidget: (_, _, _) => Container(
                        color: palette.elevated,
                        alignment: Alignment.center,
                        child: Icon(Icons.person_rounded, color: palette.textMuted),
                      ),
                    ),
            ),
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(profile.ign, style: Theme.of(context).textTheme.titleLarge, maxLines: 1, overflow: TextOverflow.ellipsis),
                const SizedBox(height: 2),
                Text('ID ${profile.playerId} · Zone ${profile.zoneId}', style: Theme.of(context).textTheme.bodySmall),
                const SizedBox(height: AppSpacing.xs),
                Wrap(
                  spacing: AppSpacing.sm,
                  children: [
                    if (profile.level != null) _Badge(label: 'Level ${profile.level}'),
                    if (profile.rankLevel != null) _Badge(label: 'Rank ${profile.rankLevel}'),
                    if (profile.rankName != null) _Badge(label: profile.rankName!),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _Badge extends StatelessWidget {
  const _Badge({required this.label});
  final String label;

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.sm, vertical: 2),
      decoration: BoxDecoration(color: palette.accentSoft, borderRadius: BorderRadius.circular(999)),
      child: Text(label, style: Theme.of(context).textTheme.labelSmall?.copyWith(color: palette.accent)),
    );
  }
}

class _StatsGrid extends StatelessWidget {
  const _StatsGrid({required this.stats});
  final PlayerStats stats;

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    final wr = stats.winRate;
    final tiles = <Widget>[
      _StatTile(label: 'Matches', value: stats.totalMatches?.toString() ?? '—'),
      _StatTile(label: 'Wins', value: stats.wins?.toString() ?? '—'),
      _StatTile(
        label: 'Win rate',
        value: wr == null ? '—' : '${(wr * 100).toStringAsFixed(1)}%',
        color: wr == null ? null : (wr >= 0.5 ? palette.positive : palette.negative),
      ),
      _StatTile(label: 'Avg score', value: stats.avgScore == null ? '—' : stats.avgScore!.toStringAsFixed(1)),
      _StatTile(label: 'MVP', value: stats.mvpCount?.toString() ?? '—'),
      _StatTile(label: 'Best streak', value: stats.winStreak?.toString() ?? '—'),
    ];

    return AppCard(
      child: Wrap(
        runSpacing: AppSpacing.md,
        children: [
          for (final tile in tiles)
            SizedBox(width: (MediaQuery.sizeOf(context).width - AppSpacing.gutter * 2 - AppSpacing.lg * 2) / 3, child: tile),
        ],
      ),
    );
  }
}

class _StatTile extends StatelessWidget {
  const _StatTile({required this.label, required this.value, this.color});
  final String label;
  final String value;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          value,
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                color: color ?? palette.textPrimary,
                fontFeatures: const [FontFeature.tabularFigures()],
              ),
        ),
        Text(label, style: Theme.of(context).textTheme.labelSmall),
      ],
    );
  }
}

class _MatchTile extends StatelessWidget {
  const _MatchTile({required this.match});
  final PlayerMatch match;

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    final color = match.won ? palette.positive : palette.negative;
    final when = _relative(match.playedAt);

    return AppCard(
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md, vertical: AppSpacing.md),
      borderColor: color.withValues(alpha: 0.35),
      child: Row(
        children: [
          Container(width: 3, height: 36, decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(2))),
          const SizedBox(width: AppSpacing.md),
          SizedBox(
            width: 34,
            height: 34,
            child: match.heroIcon == null || match.heroIcon!.isEmpty
                ? Container(
                    decoration: BoxDecoration(color: palette.elevated, shape: BoxShape.circle),
                    alignment: Alignment.center,
                    child: Icon(Icons.shield_outlined, size: 16, color: palette.textMuted),
                  )
                : ClipOval(
                    child: CachedNetworkImage(
                      imageUrl: match.heroIcon!,
                      fit: BoxFit.cover,
                      placeholder: (_, _) => Container(color: palette.elevated),
                      errorWidget: (_, _, _) => Container(color: palette.elevated),
                    ),
                  ),
          ),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Flexible(
                      child: Text(
                        match.heroName ?? 'Unknown hero',
                        style: Theme.of(context).textTheme.titleSmall,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    if (match.mvp) ...[
                      const SizedBox(width: AppSpacing.xs),
                      _Badge(label: 'MVP'),
                    ],
                  ],
                ),
                Text(
                  '${match.kills} / ${match.deaths} / ${match.assists}   ·   ${match.kda.toStringAsFixed(2)} KDA'
                  '${when == null ? '' : '   ·   $when'}',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(color: palette.textMuted),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          const SizedBox(width: AppSpacing.sm),
          Text(
            match.won ? 'WIN' : 'LOSS',
            style: Theme.of(context).textTheme.labelMedium?.copyWith(color: color, fontWeight: FontWeight.w700),
          ),
        ],
      ),
    );
  }

  static String? _relative(DateTime? at) {
    if (at == null) return null;
    final diff = DateTime.now().toUtc().difference(at.toUtc());
    if (diff.inMinutes < 1) return 'just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    if (diff.inDays < 30) return '${diff.inDays}d ago';
    return '${(diff.inDays / 30).floor()}mo ago';
  }
}

class _HeroChip extends StatelessWidget {
  const _HeroChip({required this.hero});
  final FrequentHero hero;

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    final wr = hero.winRate;
    return SizedBox(
      width: 104,
      child: AppCard(
        padding: const EdgeInsets.all(AppSpacing.sm),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                SizedBox(
                  width: 26,
                  height: 26,
                  child: hero.heroIcon == null || hero.heroIcon!.isEmpty
                      ? Container(
                          decoration: BoxDecoration(color: palette.elevated, shape: BoxShape.circle),
                          alignment: Alignment.center,
                          child: Icon(Icons.shield_outlined, size: 14, color: palette.textMuted),
                        )
                      : ClipOval(
                          child: CachedNetworkImage(
                            imageUrl: hero.heroIcon!,
                            fit: BoxFit.cover,
                            placeholder: (_, _) => Container(color: palette.elevated),
                            errorWidget: (_, _, _) => Container(color: palette.elevated),
                          ),
                        ),
                ),
                const SizedBox(width: AppSpacing.xs),
                Expanded(
                  child: Text(
                    hero.heroName ?? '—',
                    style: Theme.of(context).textTheme.labelMedium,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.xs),
            Text(
              wr == null ? '—' : '${(wr * 100).toStringAsFixed(0)}% WR',
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    color: wr == null ? palette.textMuted : (wr >= 0.5 ? palette.positive : palette.negative),
                  ),
            ),
            Text('${hero.totalMatches ?? '—'} matches', style: Theme.of(context).textTheme.labelSmall),
          ],
        ),
      ),
    );
  }
}
