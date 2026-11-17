import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart' show describeError;
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../shared/widgets/app_card.dart';
import '../../../shared/widgets/state_views.dart';
import 'auth_providers.dart';
import 'google_sign_in_button.dart';

/// Shown when nobody is signed in. Google is the only way in.
class SignInView extends ConsumerWidget {
  const SignInView({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final palette = AppPalette.of(context);
    final config = ref.watch(authConfigProvider);
    final action = ref.watch(authControllerProvider);

    return ListView(
      padding: const EdgeInsets.all(AppSpacing.gutter),
      children: [
        Text('Sign in', style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: AppSpacing.xs),
        Text(
          'MLBB Tracker accounts are created with Google. There is no other '
          'way to sign in or register.',
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
                  Text('What Google verifies', style: Theme.of(context).textTheme.titleSmall),
                ],
              ),
              const SizedBox(height: AppSpacing.sm),
              const _Line(
                icon: Icons.check_circle_outline_rounded,
                text: 'That you are a real Google account, and its verified email.',
              ),
              const _Line(
                icon: Icons.block_rounded,
                text: 'Nothing about Moonton. Your Moonton password is never asked for or stored.',
              ),
              const _Line(
                icon: Icons.edit_outlined,
                text: 'Your username and MLBB ID are typed in by you. The MLBB ID is '
                    'self-declared - it is never checked against the game.',
              ),
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.lg),
        config.when(
          loading: () => const Padding(
            padding: EdgeInsets.all(AppSpacing.lg),
            child: Center(child: CircularProgressIndicator()),
          ),
          error: (error, _) => ErrorView(
            message: describeError(error),
            onRetry: () => ref.invalidate(authConfigProvider),
          ),
          data: (cfg) {
            final clientId = cfg.googleClientId;
            if (!cfg.googleSignInEnabled || clientId == null || clientId.isEmpty) {
              return const _NotConfiguredCard();
            }
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                GoogleSignInButton(
                  clientId: clientId,
                  busy: action is AuthBusy,
                  onCredential: (credential) => ref
                      .read(authControllerProvider.notifier)
                      .signInWithGoogle(credential),
                  onError: (message) =>
                      ref.read(authControllerProvider.notifier).fail(message),
                ),
                if (action is AuthBusy) ...[
                  const SizedBox(height: AppSpacing.md),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const SizedBox(
                        width: 14,
                        height: 14,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                      const SizedBox(width: AppSpacing.sm),
                      Text(
                        'Verifying with Google...',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ],
              ],
            );
          },
        ),
        if (action is AuthFailure) ...[
          const SizedBox(height: AppSpacing.md),
          _FailureBanner(message: action.message),
        ],
        const SizedBox(height: AppSpacing.xl),
        Text(
          'Signing in does not give the app access to your Moonton account. Real '
          'match statistics still require the in-game verification code on the '
          'next step.',
          style: Theme.of(context)
              .textTheme
              .bodySmall
              ?.copyWith(color: palette.textMuted),
        ),
      ],
    );
  }
}

class _NotConfiguredCard extends StatelessWidget {
  const _NotConfiguredCard();

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
              Icon(Icons.settings_outlined, color: palette.warning, size: 20),
              const SizedBox(width: AppSpacing.sm),
              Expanded(
                child: Text(
                  'Google sign-in is not configured',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.sm),
          Text(
            'This server has no Google OAuth client ID, so no account can be '
            'created right now. Nothing is faked: the app will not show a '
            'button that cannot work.',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: AppSpacing.sm),
          Text(
            'To enable it, set MLBB_GOOGLE_CLIENT_ID to an OAuth 2.0 web client '
            'ID and add this site to its authorized JavaScript origins. See '
            'docs/DEPLOYMENT.md.',
            style: Theme.of(context)
                .textTheme
                .bodySmall
                ?.copyWith(color: palette.textMuted),
          ),
        ],
      ),
    );
  }
}

class _FailureBanner extends StatelessWidget {
  const _FailureBanner({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    return AppCard(
      borderColor: palette.negative.withValues(alpha: 0.5),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.error_outline_rounded, color: palette.negative, size: 20),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Text(message, style: Theme.of(context).textTheme.bodySmall),
          ),
        ],
      ),
    );
  }
}

class _Line extends StatelessWidget {
  const _Line({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 16, color: palette.textMuted),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Text(text, style: Theme.of(context).textTheme.bodySmall),
          ),
        ],
      ),
    );
  }
}
