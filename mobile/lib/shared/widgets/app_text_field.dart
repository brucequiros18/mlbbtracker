import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Reusable labelled text input used for player/zone search and filters.
class AppTextField extends StatelessWidget {
  const AppTextField({
    super.key,
    required this.label,
    this.controller,
    this.hint,
    this.keyboardType,
    this.textInputAction,
    this.onSubmitted,
    this.helper,
    this.error,
    this.digitsOnly = false,
    this.maxLength,
  });

  final String label;
  final TextEditingController? controller;
  final String? hint;
  final TextInputType? keyboardType;
  final TextInputAction? textInputAction;
  final ValueChanged<String>? onSubmitted;
  final String? helper;
  final String? error;
  final bool digitsOnly;
  final int? maxLength;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      keyboardType: keyboardType,
      textInputAction: textInputAction,
      onSubmitted: onSubmitted,
      inputFormatters: digitsOnly ? [FilteringTextInputFormatter.digitsOnly] : null,
      maxLength: maxLength,
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        helperText: helper,
        errorText: error,
        counterText: '',
      ),
    );
  }
}
