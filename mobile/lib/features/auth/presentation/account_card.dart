import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../shared/widgets/app_button.dart';
import '../../../shared/widgets/app_card.dart';
import '../../../shared/widgets/app_text_field.dart';
import '../domain/account.dart';
import 'auth_providers.dart';

/// The signed-in account: Google identity plus the app-only profile.
class AccountCard extends ConsumerWidget {
  const AccountCard({super.key, required this.account});

  final Account account;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final palette = AppPalette.of(context);
    return AppCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _Avatar(account: account),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  account.displayName,
                  style: Theme.of(context).textTheme.titleMedium,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 2),
                Text(
                  account.email,
                  style: Theme.of(context)
                      .textTheme
                      .bodySmall
                      ?.copyWith(color: palette.textMuted),
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: AppSpacing.sm),
                Wrap(
                  spacing: AppSpacing.sm,
                  runSpacing: AppSpacing.xs,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  children: [
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.badge_outlined, size: 14, color: palette.textMuted),
                        const SizedBox(width: 4),
                        Text(
                          'MLBB ID ${account.mlbbId ?? 'not set'}',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                    const _SelfDeclaredBadge(),
                  ],
                ),
              ],
            ),
          ),
          IconButton(
            tooltip: 'Edit profile',
            icon: const Icon(Icons.edit_outlined),
            onPressed: () => showDialog<void>(
              context: context,
              builder: (_) => _EditProfileDialog(account: account),
            ),
          ),
        ],
      ),
    );
  }
}

class _Avatar extends StatelessWidget {
  const _Avatar({required this.account});

  final Account account;

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    final fallback = Container(
      width: 44,
      height: 44,
      alignment: Alignment.center,
      color: palette.accentSoft,
      child: Text(
        account.initials,
        style: Theme.of(context)
            .textTheme
            .titleMedium
            ?.copyWith(color: palette.accent),
      ),
    );
    final url = account.pictureUrl;
    return ClipOval(
      child: SizedBox(
        width: 44,
        height: 44,
        child: url == null
            ? fallback
            : Image.network(
                url,
                fit: BoxFit.cover,
                errorBuilder: (_, _, _) => fallback,
              ),
      ),
    );
  }
}

class _SelfDeclaredBadge extends StatelessWidget {
  const _SelfDeclaredBadge();

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    return Tooltip(
      message: 'Typed in by you. Never verified against Moonton.',
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
        decoration: BoxDecoration(
          color: palette.accentSoft,
          borderRadius: BorderRadius.circular(999),
        ),
        child: Text(
          'self-declared',
          style: Theme.of(context)
              .textTheme
              .labelSmall
              ?.copyWith(color: palette.accent),
        ),
      ),
    );
  }
}

class _EditProfileDialog extends ConsumerStatefulWidget {
  const _EditProfileDialog({required this.account});

  final Account account;

  @override
  ConsumerState<_EditProfileDialog> createState() => _EditProfileDialogState();
}

class _EditProfileDialogState extends ConsumerState<_EditProfileDialog> {
  late final TextEditingController _username =
      TextEditingController(text: widget.account.username ?? '');
  late final TextEditingController _mlbbId =
      TextEditingController(text: widget.account.mlbbId ?? '');
  final _currentPassword = TextEditingController();
  final _newPassword = TextEditingController();
  String? _error;

  @override
  void dispose() {
    _username.dispose();
    _mlbbId.dispose();
    _currentPassword.dispose();
    _newPassword.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final username = _username.text.trim();
    final mlbbId = _mlbbId.text.trim();
    final current = _currentPassword.text;
    final newPassword = _newPassword.text;

    if (current.isEmpty) {
      setState(() => _error = 'Enter your app password to confirm the change.');
      return;
    }
    if (newPassword.isNotEmpty && newPassword.length < 8) {
      setState(() => _error = 'The new password must be at least 8 characters.');
      return;
    }

    setState(() => _error = null);
    final ok = await ref.read(authControllerProvider.notifier).updateProfile(
          username: username.isEmpty ? null : username,
          mlbbId: mlbbId.isEmpty ? null : mlbbId,
          currentPassword: current,
          newPassword: newPassword.isEmpty ? null : newPassword,
        );
    if (!mounted) return;
    if (ok) {
      ref.read(authControllerProvider.notifier).clearError();
      Navigator.of(context).pop();
    } else {
      final state = ref.read(authControllerProvider);
      setState(() {
        _error = state is AuthFailure ? state.message : 'Could not save.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    final busy = ref.watch(authControllerProvider) is AuthBusy;

    return AlertDialog(
      title: const Text('Edit profile'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            AppTextField(label: 'Username', controller: _username, maxLength: 24),
            const SizedBox(height: AppSpacing.md),
            AppTextField(
              label: 'MLBB ID',
              controller: _mlbbId,
              digitsOnly: true,
              keyboardType: TextInputType.number,
              maxLength: 20,
              helper: 'Self-declared. Never verified against Moonton.',
            ),
            const SizedBox(height: AppSpacing.md),
            AppTextField(
              label: 'App password',
              controller: _currentPassword,
              obscureText: true,
              helper: 'Confirms the change. It is not a sign-in method.',
            ),
            const SizedBox(height: AppSpacing.md),
            AppTextField(
              label: 'New password (optional)',
              controller: _newPassword,
              obscureText: true,
            ),
            if (_error != null) ...[
              const SizedBox(height: AppSpacing.md),
              Text(
                _error!,
                style: Theme.of(context)
                    .textTheme
                    .bodySmall
                    ?.copyWith(color: palette.negative),
              ),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: busy ? null : () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        AppPrimaryButton(
          label: 'Save',
          loading: busy,
          expand: false,
          onPressed: busy ? null : _save,
        ),
      ],
    );
  }
}
