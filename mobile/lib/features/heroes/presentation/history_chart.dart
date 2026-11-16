import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../shared/widgets/stat_tile.dart' show formatPercent;
import '../domain/hero.dart';

/// Win-rate line chart for the snapshots **this backend recorded itself**.
///
/// Deliberately separate from [HeroTrendChart] (the provider's own timeline):
/// the provider trend is upstream truth, this is our observation log. The two
/// use different colours so they are never confused, and a single point is not
/// drawn as a line because a one-point "trend" would imply movement that was
/// never observed.
class HeroHistoryChart extends StatelessWidget {
  const HeroHistoryChart({super.key, required this.points});

  final List<HeroHistoryPoint> points;

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);

    if (points.isEmpty) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: AppSpacing.md),
        child: Text(
          'No snapshots recorded yet. They accumulate daily as the backend observes live rankings.',
          style: Theme.of(context).textTheme.bodySmall,
        ),
      );
    }

    if (points.length == 1) {
      final only = points.first;
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'One snapshot recorded on ${_shortDate(only.capturedOn)} '
              '(${formatPercent(only.winRate)} win rate). '
              'A line appears after the next daily capture.',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      );
    }

    final spots = <FlSpot>[
      for (var i = 0; i < points.length; i++) FlSpot(i.toDouble(), points[i].winRate),
    ];
    final rates = points.map((p) => p.winRate).toList();
    final double minY = (rates.reduce((a, b) => a < b ? a : b) - 0.005).clamp(0.0, 1.0);
    final double maxY = (rates.reduce((a, b) => a > b ? a : b) + 0.005).clamp(0.0, 1.0);
    final double yInterval = ((maxY - minY) / 3).clamp(0.001, 1.0);
    final int step = ((points.length - 1) / 2).ceil();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          height: 180,
          child: LineChart(
            LineChartData(
              minX: 0,
              maxX: (points.length - 1).toDouble(),
              minY: minY,
              maxY: maxY,
              gridData: FlGridData(
                show: true,
                drawVerticalLine: false,
                horizontalInterval: yInterval,
                getDrawingHorizontalLine: (v) => FlLine(
                  color: palette.border,
                  strokeWidth: 1,
                ),
              ),
              titlesData: FlTitlesData(
                topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    reservedSize: 46,
                    interval: yInterval,
                    getTitlesWidget: (value, _) => Text(
                      formatPercent(value, decimals: 1),
                      style: Theme.of(context).textTheme.labelSmall,
                    ),
                  ),
                ),
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    reservedSize: 22,
                    interval: 1,
                    getTitlesWidget: (value, _) {
                      final index = value.toInt();
                      if (index < 0 || index >= points.length) return const SizedBox.shrink();
                      final isEdge = index == 0 || index == points.length - 1;
                      if (!isEdge && step > 0 && index % step != 0) {
                        return const SizedBox.shrink();
                      }
                      return Padding(
                        padding: const EdgeInsets.only(top: AppSpacing.xs),
                        child: Text(
                          _shortDate(points[index].capturedOn),
                          style: Theme.of(context).textTheme.labelSmall,
                        ),
                      );
                    },
                  ),
                ),
              ),
              borderData: FlBorderData(show: false),
              lineBarsData: [
                LineChartBarData(
                  spots: spots,
                  isCurved: true,
                  barWidth: 2.5,
                  color: palette.positive,
                  isStrokeCapRound: true,
                  dotData: FlDotData(
                    show: true,
                    getDotPainter: (spot, _, _, _) => FlDotCirclePainter(
                      radius: 3,
                      color: palette.positive,
                      strokeWidth: 0,
                    ),
                  ),
                  belowBarData: BarAreaData(
                    show: true,
                    color: palette.positive.withValues(alpha: 0.14),
                  ),
                ),
              ],
            ),
            duration: const Duration(milliseconds: 250),
          ),
        ),
        const SizedBox(height: AppSpacing.sm),
        Text(
          '${points.length} daily snapshot${points.length == 1 ? '' : 's'} recorded '
          '(${_shortDate(points.first.capturedOn)} → ${_shortDate(points.last.capturedOn)})',
          style: Theme.of(context).textTheme.labelSmall,
        ),
      ],
    );
  }

  static String _shortDate(String iso) {
    final parts = iso.split('-');
    if (parts.length < 3) return iso;
    return '${parts[1]}-${parts[2]}';
  }
}
