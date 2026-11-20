<?php

namespace App\Support;

/**
 * Helpers for joining provider data by hero name.
 */
final class HeroName
{
    /**
     * Case/spacing/symbol-insensitive key used to join data across providers.
     *
     * "Luo Yi" -> "luoyi", "X.Borg" -> "xborg", "Yi Sun-shin" -> "yisunshin".
     */
    public static function normalize(string $value): string
    {
        return (string) preg_replace('/[^a-z0-9]/', '', strtolower($value));
    }
}
