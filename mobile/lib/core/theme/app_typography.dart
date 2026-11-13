import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import 'app_colors.dart';

/// Typography scale.
///
/// Manrope for headings, Inter for body copy and statistics. Numeric styles
/// use tabular figures so columns of stats stay aligned.
abstract final class AppTypography {
  static TextTheme textTheme(AppPalette palette) {
    final Color on = palette.textPrimary;
    final Color muted = palette.textSecondary;

    final TextTheme body = GoogleFonts.interTextTheme().apply(
      bodyColor: on,
      displayColor: on,
    );
    final TextTheme display = GoogleFonts.manropeTextTheme().apply(
      bodyColor: on,
      displayColor: on,
    );

    return body.copyWith(
      displayLarge: display.displayLarge?.copyWith(fontWeight: FontWeight.w800, letterSpacing: -0.5),
      displayMedium: display.displayMedium?.copyWith(fontWeight: FontWeight.w800, letterSpacing: -0.5),
      displaySmall: display.displaySmall?.copyWith(fontWeight: FontWeight.w700),
      headlineLarge: display.headlineLarge?.copyWith(fontWeight: FontWeight.w700),
      headlineMedium: display.headlineMedium?.copyWith(fontWeight: FontWeight.w700),
      headlineSmall: display.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
      titleLarge: display.titleLarge?.copyWith(fontWeight: FontWeight.w700, fontSize: 20),
      titleMedium: display.titleMedium?.copyWith(fontWeight: FontWeight.w600, fontSize: 16),
      titleSmall: display.titleSmall?.copyWith(fontWeight: FontWeight.w600, fontSize: 14),
      bodyLarge: body.bodyLarge?.copyWith(fontSize: 16, height: 1.45),
      bodyMedium: body.bodyMedium?.copyWith(fontSize: 14, height: 1.45, color: muted),
      bodySmall: body.bodySmall?.copyWith(fontSize: 13, height: 1.4, color: muted),
      labelLarge: body.labelLarge?.copyWith(fontWeight: FontWeight.w600, fontSize: 14),
      labelMedium: body.labelMedium?.copyWith(fontWeight: FontWeight.w600, fontSize: 12, color: muted),
      labelSmall: body.labelSmall?.copyWith(fontWeight: FontWeight.w600, fontSize: 11, color: palette.textMuted, letterSpacing: 0.6),
    );
  }

  /// Style for large numeric statistics (win rate, KDA, …).
  static TextStyle statNumber(AppPalette palette, {double size = 22}) =>
      GoogleFonts.inter(
        fontSize: size,
        fontWeight: FontWeight.w700,
        color: palette.textPrimary,
        fontFeatures: const [FontFeature.tabularFigures()],
      );
}
