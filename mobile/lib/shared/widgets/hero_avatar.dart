import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_radius.dart';
import '../../core/theme/app_spacing.dart';

/// Circular hero portrait with caching and a graceful fallback.
class HeroAvatar extends StatelessWidget {
  const HeroAvatar({
    super.key,
    required this.imageUrl,
    this.size = 48,
    this.name,
  });

  final String? imageUrl;
  final double size;
  final String? name;

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    final placeholder = Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: palette.elevated,
        borderRadius: BorderRadius.circular(AppRadius.md),
      ),
      alignment: Alignment.center,
      child: Text(
        (name?.isNotEmpty ?? false) ? name!.characters.first.toUpperCase() : '?',
        style: Theme.of(context).textTheme.titleMedium,
      ),
    );

    return ClipRRect(
      borderRadius: BorderRadius.circular(AppRadius.sm),
      child: SizedBox(
        width: size,
        height: size,
        child: (imageUrl == null || imageUrl!.isEmpty)
            ? placeholder
            : CachedNetworkImage(
                imageUrl: imageUrl!,
                fit: BoxFit.cover,
                placeholder: (_, _) => Container(
                  width: size,
                  height: size,
                  color: palette.elevated,
                ),
                errorWidget: (_, _, _) => placeholder,
              ),
      ),
    );
  }
}

/// Small role pill used on hero cards and detail headers.
class RoleTag extends StatelessWidget {
  const RoleTag({super.key, required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    final palette = AppPalette.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.sm, vertical: 3),
      decoration: BoxDecoration(
        color: palette.accentSoft,
        borderRadius: AppRadius.chip,
      ),
      child: Text(
        label,
        style: Theme.of(context).textTheme.labelSmall?.copyWith(color: palette.accent),
      ),
    );
  }
}
