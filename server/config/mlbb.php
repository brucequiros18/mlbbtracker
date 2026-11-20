<?php

/**
 * MLBB Tracker configuration.
 *
 * Values can be overridden with environment variables prefixed `MLBB_`
 * (for example `MLBB_RONE_BASE_URL`) or via a `.env` file.
 */
return [
    'app_name' => env('MLBB_APP_NAME', 'MLBB Tracker API'),

    'api_v1_prefix' => '/api/v1',

    // Provider endpoints (real, verified in docs/API_DOCUMENTATION.md).
    'rone_base_url' => env('MLBB_RONE_BASE_URL', 'https://arena.rone.dev/api'),
    'mlbbdex_base_url' => env('MLBB_MLBBDEX_BASE_URL', 'https://mlbbdex.com/api/v1'),

    // Provider toggles. At least one hero provider must be enabled.
    'enable_rone' => (bool) env('MLBB_ENABLE_RONE', true),
    'enable_mlbbdex' => (bool) env('MLBB_ENABLE_MLBBDEX', true),
    // Player data requires an authenticated source, which is not enabled.
    'enable_player_lookup' => (bool) env('MLBB_ENABLE_PLAYER_LOOKUP', false),

    'http_timeout' => (float) env('MLBB_HTTP_TIMEOUT', 15),
    'http_user_agent' => env('MLBB_HTTP_USER_AGENT', 'mlbb-tracker-backend/0.1 (+https://example.local)'),

    // Cache TTLs (seconds).
    'cache_ttl_catalog' => (int) env('MLBB_CACHE_TTL_CATALOG', 6 * 60 * 60),
    'cache_ttl_rankings' => (int) env('MLBB_CACHE_TTL_RANKINGS', 60 * 60),
    'cache_ttl_detail' => (int) env('MLBB_CACHE_TTL_DETAIL', 6 * 60 * 60),
    'cache_ttl_health' => (int) env('MLBB_CACHE_TTL_HEALTH', 60),

    // Google sign-in - the app's only credential. The value is the OAuth 2.0
    // *web* client ID from Google Cloud Console; it is public (it ships to the
    // browser), so the API exposes it via GET /api/v1/auth/config.
    // Empty = not configured: sign-in answers 503 GOOGLE_NOT_CONFIGURED and
    // the app shows that state instead of a button that cannot work.
    'google_client_id' => env('MLBB_GOOGLE_CLIENT_ID', ''),

    // How long an app account session stays valid (sliding, refreshed on use).
    'user_session_ttl_days' => (int) env('MLBB_USER_SESSION_TTL_DAYS', 30),

    // Published app releases (APK + latest.json manifest), served at
    // /download and /downloads/<file>. Empty = auto-detect `<repo>/releases`.
    'releases_dir' => env('MLBB_RELEASES_DIR', ''),

    // React web build served by this app (same origin as the API).
    // Empty = auto-detect `<repo>/web/dist` copied into `public/app`.
    'web_root' => env('MLBB_WEB_ROOT', ''),
];
