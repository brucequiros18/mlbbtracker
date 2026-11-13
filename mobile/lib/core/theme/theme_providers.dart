import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Active theme mode. Dark is the initial default; light is fully supported.
final themeModeProvider = StateProvider<ThemeMode>((ref) => ThemeMode.dark);
