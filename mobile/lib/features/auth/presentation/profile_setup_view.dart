import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../shared/widgets/app_button.dart';
import '../../../shared/widgets/app_card.dart';
import '../../../shared/widgets/app_text_field.dart';
import '../domain/account.dart';
import 'auth_providers.dart';

/// Shown right after the first Google sign-in: the account exists, but the
/// player still has to choose a username, enter their MLBB ID (self-declared)
/// and set an app password.
class ProfileSetupView extends ConsumerStatefulWidget {
  const ProfileSetupView({super.key, required this.account});

  final Account account;

  @override
  ConsumerState<ProfileSetupView> createState() => _ProfileSetupViewState();
}

class _ProfileSetupViewState extends ConsumerState<ProfileSetupView> {
  final _username = TextEditingController();
  final _mlbbId = TextEditingController();
  final _password = TextEditingController();
  final _confirm = TextEditingController();

  String? _usernameError;
  String? _mlbbIdError;
  String? _passwordError;
  String? _confirmError;

  @override
  void dispose() {
    _username.dispose();
    _mlbbId.dispose();
    _password.dispose();
    _confirm.dispose();
    super.dispose();
  }

  Future<void> _submit(AuthConfig config) async {
    final username = _username.text.trim();
    final mlbbId = _mlbbId.text.trim();
    final password = _password.text;
    final confirm = _confirm.text;

    final usernameOk = RegExp(config.usernamePattern).hasMatch(username);
    final mlbbIdOk = RegExp(config.mlbbIdPattern).hasMatch(mlbbId);
    final passwordOk = password.length >= config.minPasswordLength;

    setState(() {
      _usernameError = usernameOk
          ? null
          : 'Use 3-24 letters, numbers or underscores';
      _mlbbIdError = mlbbIdOk
          ? null
          : 'Enter the numeric ID from your in-game profile';
      _passwordError = passwordOk
          ? null
          : 'Use at least ${config.minPasswordLength} characters';
      _confirmError = password == confirm ? null : 'Passwords do not match';
    });
    if (!usernameOk || !mlbbIdOk || !passwordOk || password != confirm) return;

    FocusScope.of(context).unfocus();
    await ref.read(authControllerProvider.notifier).register(
          username: username,
          mlbbId: mlbbId,
          password: password,
        );
  }

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    final config = ref.watch(authConfigProvider).valueOrNull;
    final action = ref.watch(authControllerProvider);
    final busy = action is AuthBusy;

    if (config == null) {
      return const Center(child: CircularProgressIndicator());
    }

    return ListView(
      padding: const EdgeInsets.all(AppSpacing.gutter),
      children: [
        Text('Finish your account', style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: AppSpacing.xs),
        Text(
          'Signed in as ${widget.account.email}',
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
                  Icon(Icons.badge_outlined, color: palette.accent, size: 20),
                  const SizedBox(width: AppSpacing.sm),
                  Expanded(
                    child: Text(
                      'Your MLBB Tracker profile',
                      style: Theme.of(context).textTheme.titleSmall,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.sm),
              Text(
                'The username is how you appear in the app. The MLBB ID is '
                'self-declared: it is stored as typed and never verified against '
                'Moonton. The app password is app-only - Google remains the only '
                'way to sign in.',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.lg),
        AppTextField(
          label: 'Username',
          hint: 'e.g. AshKetchum',
          controller: _username,
          maxLength: 24,
          helper: '3-24 letters, numbers or underscores. Unique, ignoring case.',
          error: _usernameError,
        ),
        const SizedBox(height: AppSpacing.md),
        AppTextField(
          label: 'MLBB ID',
          hint: 'e.g. 123456789',
          controller: _mlbbId,
          digitsOnly: true,
          keyboardType: TextInputType.number,
          maxLength: 20,
          helper: 'Self-declared. We never check it against the game.',
          error: _mlbbIdError,
        ),
        const SizedBox(height: AppSpacing.md),
        AppTextField(
          label: 'App password',
          hint: 'At least ${config.minPasswordLength} characters',
          controller: _password,
          obscureText: true,
          maxLength: config.maxPasswordLength,
          helper: 'Stored only as a salted hash. Never sent to Moonton, never '
              'used to sign in.',
          error: _passwordError,
        ),
        const SizedBox(height: AppSpacing.md),
        AppTextField(
          label: 'Confirm password',
          controller: _confirm,
          obscureText: true,
          maxLength: config.maxPasswordLength,
          error: _confirmError,
          onSubmitted: (_) => busy ? null : _submit(config),
        ),
        const SizedBox(height: AppSpacing.lg),
        AppPrimaryButton(
          label: 'Create my profile',
          icon: Icons.check_rounded,
          loading: busy,
          onPressed: busy ? null : () => _submit(config),
        ),
        if (action is AuthFailure) ...[
          const SizedBox(height: AppSpacing.md),
          AppCard(
            borderColor: palette.negative.withValues(alpha: 0.5),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.error_outline_rounded, color: palette.negative, size: 20),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: Text(
                    action.message,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
              ],
            ),
          ),
        ],
        const SizedBox(height: AppSpacing.sm),
        TextButton(
          onPressed: busy
              ? null
              : () => ref.read(authControllerProvider.notifier).signOut(),
          child: const Text('Use a different Google account'),
        ),
      ],
    );
  }
}
