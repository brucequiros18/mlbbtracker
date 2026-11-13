import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../shared/widgets/stat_tile.dart' show formatPercent;
import '../domain/hero.dart';

/// Daily win-rate line chart for a single hero.
///
/// Requires at least two points; otherwise it degrades to a short caption
/// instead of drawing a misleading chart.
class HeroTrendChart extends StatelessWidget {
  const HeroTrendChart({super.key, required this.points});

  final List<HeroTrendPoint> points;

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);

    if (points.length < 2) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: AppSpacing.md),
        child: Text(
          'Not enough history to draw a trend.',
          style: Theme.of(context).textTheme.bodySmall,
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

    return SizedBox(
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
                      _shortDate(points[index].date),
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
              color: palette.accent,
              isStrokeCapRound: true,
              dotData: FlDotData(
                show: true,
                getDotPainter: (spot, _, _, _) => FlDotCirclePainter(
                  radius: 3,
                  color: palette.accent,
                  strokeWidth: 0,
                ),
              ),
              belowBarData: BarAreaData(
                show: true,
                color: palette.accentSoft,
              ),
            ),
          ],
        ),
        duration: const Duration(milliseconds: 250),
      ),
    );
  }

  static String _shortDate(String iso) {
    final parts = iso.split('-');
    if (parts.length < 3) return iso;
    return '${parts[1]}-${parts[2]}';
  }
}
