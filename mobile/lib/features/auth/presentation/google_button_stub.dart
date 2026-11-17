import 'package:flutter/widgets.dart';

/// Non-web platforms cannot render Google Identity Services' button, so the
/// sign-in screen uses its own native button instead. This stub keeps the
/// conditional import compiling everywhere.
Widget buildGoogleButton({required double width}) => const SizedBox.shrink();
