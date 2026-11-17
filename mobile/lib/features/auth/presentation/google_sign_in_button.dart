import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../shared/widgets/app_button.dart';
import 'google_button_stub.dart'
    if (dart.library.js_interop) 'google_button_web.dart' as web_button;

/// The plugin may be initialized only once per process.
Future<void>? _initialization;

Future<void> _ensureInitialized(String clientId) async {
  final existing = _initialization;
  if (existing != null) return existing;
  final future = kIsWeb
      ? GoogleSignIn.instance.initialize(clientId: clientId)
      : GoogleSignIn.instance.initialize(serverClientId: clientId);
  _initialization = future;
  try {
    await future;
  } catch (_) {
    // Allow a retry after a configuration/network failure.
    _initialization = null;
    rethrow;
  }
}

bool get _googleSupported {
  if (kIsWeb) return true;
  return defaultTargetPlatform == TargetPlatform.android ||
      defaultTargetPlatform == TargetPlatform.iOS;
}

/// Starts the Google sign-in flow.
///
/// * **Web** - Google Identity Services only allows sign-in from its own
///   button, so the official button is rendered and the ID token arrives on
///   `authenticationEvents`.
/// * **Android / iOS** - the native account picker is used.
///
/// Either way the app receives a Google **ID token** and sends it to the
/// backend, which is the only place it is verified.
class GoogleSignInButton extends StatefulWidget {
  const GoogleSignInButton({
    super.key,
    required this.clientId,
    required this.onCredential,
    required this.onError,
    this.busy = false,
  });

  final String clientId;
  final ValueChanged<String> onCredential;
  final ValueChanged<String> onError;
  final bool busy;

  @override
  State<GoogleSignInButton> createState() => _GoogleSignInButtonState();
}

class _GoogleSignInButtonState extends State<GoogleSignInButton> {
  bool _ready = false;
  String? _problem;
  StreamSubscription<GoogleSignInAuthenticationEvent>? _events;

  @override
  void initState() {
    super.initState();
    _start();
  }

  @override
  void dispose() {
    _events?.cancel();
    super.dispose();
  }

  Future<void> _start() async {
    if (!_googleSupported) {
      setState(
        () => _problem = 'Google sign-in is available in the web and Android apps.',
      );
      return;
    }
    try {
      await _ensureInitialized(widget.clientId);
      if (!mounted) return;
      _events = GoogleSignIn.instance.authenticationEvents.listen(
        _onEvent,
        onError: (Object error) => widget.onError(_message(error)),
      );
      setState(() => _ready = true);
    } catch (error) {
      if (mounted) setState(() => _problem = _message(error));
    }
  }

  void _onEvent(GoogleSignInAuthenticationEvent event) {
    if (event is! GoogleSignInAuthenticationEventSignIn) return;
    final token = event.user.authentication.idToken;
    if (token == null || token.isEmpty) {
      widget.onError(
        'Google did not return an ID token. Check the OAuth client configuration.',
      );
      return;
    }
    widget.onCredential(token);
  }

  Future<void> _authenticate() async {
    try {
      final account = await GoogleSignIn.instance.authenticate();
      final token = account.authentication.idToken;
      if (token == null || token.isEmpty) {
        widget.onError(
          'Google did not return an ID token. Check the OAuth client configuration.',
        );
        return;
      }
      widget.onCredential(token);
    } on GoogleSignInException catch (error) {
      if (error.code == GoogleSignInExceptionCode.canceled) return;
      widget.onError(_message(error));
    } catch (error) {
      widget.onError(_message(error));
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_problem != null) {
      return _Notice(message: _problem!);
    }
    if (!_ready) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: AppSpacing.md),
        child: Center(
          child: SizedBox(
            width: 20,
            height: 20,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
        ),
      );
    }
    if (kIsWeb) {
      return LayoutBuilder(
        builder: (context, constraints) {
          final width =
              constraints.maxWidth.isFinite ? constraints.maxWidth : 320.0;
          return web_button.buildGoogleButton(width: width);
        },
      );
    }
    return AppPrimaryButton(
      label: 'Continue with Google',
      icon: Icons.account_circle_outlined,
      loading: widget.busy,
      onPressed: widget.busy ? null : _authenticate,
    );
  }
}

class _Notice extends StatelessWidget {
  const _Notice({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
      child: Text(
        message,
        style: Theme.of(context)
            .textTheme
            .bodySmall
            ?.copyWith(color: palette.textMuted),
      ),
    );
  }
}

String _message(Object error) {
  if (error is GoogleSignInException) {
    final detail = error.description;
    final suffix = detail == null || detail.isEmpty ? '' : ' ($detail)';
    return switch (error.code) {
      GoogleSignInExceptionCode.canceled => 'Sign-in was cancelled.',
      GoogleSignInExceptionCode.clientConfigurationError =>
        'Google sign-in is not configured for this address. '
            'Add it to the OAuth client\'s authorized JavaScript origins.$suffix',
      GoogleSignInExceptionCode.providerConfigurationError =>
        'Google sign-in is unavailable right now. Please try again later.$suffix',
      GoogleSignInExceptionCode.uiUnavailable =>
        'Google sign-in could not open a window. Please try again.',
      _ => detail ?? 'Google sign-in failed. Please try again.',
    };
  }
  return 'Google sign-in failed. Please try again.';
}
