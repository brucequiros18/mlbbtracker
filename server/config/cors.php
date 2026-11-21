<?php

/**
 * CORS for the API.
 *
 * Same-origin requests (Laravel serving the app itself) never hit this — it
 * exists for split deployments where the app is served from a different
 * origin, such as GitHub Pages calling the Render-hosted API.
 *
 * Set MLBB_CORS_ALLOWED_ORIGINS to a comma-separated list of exact origins,
 * e.g. https://brucequiros18.github.io,http://localhost:5173
 */
return [
    'paths' => ['api/*'],

    'allowed_methods' => ['*'],

    'allowed_origins' => array_values(array_filter(array_map(
        'trim',
        explode(',', (string) env('MLBB_CORS_ALLOWED_ORIGINS', ''))
    ))),

    'allowed_origins_patterns' => [],

    'allowed_headers' => ['*'],

    'exposed_headers' => [],

    'max_age' => 3600,

    'supports_credentials' => false,
];
