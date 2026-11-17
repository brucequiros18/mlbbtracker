import 'package:flutter/widgets.dart';
import 'package:google_sign_in_web/web_only.dart' as web;

/// The official Google Identity Services button.
///
/// The GIS SDK only permits sign-in from UI it renders itself, so the app
/// cannot draw its own "Continue with Google" button on the web. This widget
/// hosts the real one; the credential arrives on `authenticationEvents`.
Widget buildGoogleButton({required double width}) {
  final clamped = width.clamp(200.0, 400.0).toDouble();
  return web.renderButton(
    configuration: web.GSIButtonConfiguration(
      type: web.GSIButtonType.standard,
      theme: web.GSIButtonTheme.filledBlack,
      size: web.GSIButtonSize.large,
      text: web.GSIButtonText.continueWith,
      shape: web.GSIButtonShape.rectangular,
      logoAlignment: web.GSIButtonLogoAlignment.center,
      minimumWidth: clamped,
    ),
  );
}
