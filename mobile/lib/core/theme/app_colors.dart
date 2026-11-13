import 'package:flutter/material.dart';

/// Central color palette for MLBB Tracker.
///
/// Design direction: **Competitive Minimalism** — a modern, professional,
/// gaming-oriented dark interface. Both a dark and a light palette are
/// defined; dark is the initial default.
@immutable
class AppPalette {
  const AppPalette({
    required this.background,
    required this.backgroundSecondary,
    required this.card,
    required this.elevated,
    required this.accent,
    required this.accentSoft,
    required this.positive,
    required this.negative,
    required this.warning,
    required this.textPrimary,
    required this.textSecondary,
    required this.textMuted,
    required this.border,
    required this.brightness,
  });

  final Color background;
  final Color backgroundSecondary;
  final Color card;
  final Color elevated;
  final Color accent;
  final Color accentSoft;
  final Color positive;
  final Color negative;
  final Color warning;
  final Color textPrimary;
  final Color textSecondary;
  final Color textMuted;
  final Color border;
  final Brightness brightness;

  /// Dark theme (default).
  static const AppPalette dark = AppPalette(
    background: Color(0xFF111318),
    backgroundSecondary: Color(0xFF171A22),
    card: Color(0xFF1B1F29),
    elevated: Color(0xFF242936),
    accent: Color(0xFF8B7CFF),
    accentSoft: Color(0x338B7CFF),
    positive: Color(0xFF39D6A3),
    negative: Color(0xFFEF6464),
    warning: Color(0xFFF5B85B),
    textPrimary: Color(0xFFF5F5F7),
    textSecondary: Color(0xFFA4A8B4),
    textMuted: Color(0xFF747B8B),
    border: Color(0xFF262B38),
    brightness: Brightness.dark,
  );

  /// Light theme.
  static const AppPalette light = AppPalette(
    background: Color(0xFFF6F7FB),
    backgroundSecondary: Color(0xFFFFFFFF),
    card: Color(0xFFFFFFFF),
    elevated: Color(0xFFEEF0F6),
    accent: Color(0xFF6C5CE7),
    accentSoft: Color(0x1F6C5CE7),
    positive: Color(0xFF149E77),
    negative: Color(0xFFD64545),
    warning: Color(0xFFB7791F),
    textPrimary: Color(0xFF14161C),
    textSecondary: Color(0xFF4B5162),
    textMuted: Color(0xFF8A90A2),
    border: Color(0xFFE2E5EE),
    brightness: Brightness.light,
  );

  static AppPalette of(BuildContext context) =>
      Theme.of(context).brightness == Brightness.dark ? dark : light;
}
