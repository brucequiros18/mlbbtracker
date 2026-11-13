import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_typography.dart';

/// Reusable statistic block: a tabular value with a short caption and an
/// optional semantic color (positive/negative).
class StatTile extends StatelessWidget {
  const StatTile({
    super.key,
    required this.label,
    required this.value,
    this.valueColor,
    this.subdued = false,
    this.align = CrossAxisAlignment.start,
  });

  final String label;
  final String value;
  final Color? valueColor;
  final bool subdued;
  final CrossAxisAlignment align;

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    return Column(
      crossAxisAlignment: align,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          value,
          style: AppTypography.statNumber(palette, size: subdued ? 18 : 22)
              .copyWith(color: valueColor ?? palette.textPrimary),
        ),
        const SizedBox(height: AppSpacing.xs),
        Text(label, style: Theme.of(context).textTheme.labelSmall, maxLines: 1, overflow: TextOverflow.ellipsis),
      ],
    );
  }
}

/// Formats a ratio (0..1) as a percentage string.
String formatPercent(double ratio, {int decimals = 1}) =>
    '${(ratio * 100).toStringAsFixed(decimals)}%';
