/// 8-point spacing system used across the application.
///
/// Every gap, padding and margin must be a multiple of 4/8 logical pixels so
/// the whole interface shares one visual rhythm.
abstract final class AppSpacing {
  static const double xxs = 2;
  static const double xs = 4;
  static const double sm = 8;
  static const double md = 12;
  static const double lg = 16;
  static const double xl = 24;
  static const double xxl = 32;
  static const double xxxl = 48;

  /// Standard horizontal page gutter.
  static const double gutter = 16;

  /// Minimum interactive touch target (accessibility).
  static const double minTouchTarget = 48;
}
