#!/bin/sh
# Container entrypoint: prepare the environment, migrate, serve.
#
# Render (and most hosts) inject configuration as real environment
# variables, which take precedence over any .env file.
set -e
cd /var/www

# A .env file must exist for artisan's file paths, but real environment
# variables (from Render) win over it.
if [ ! -f .env ]; then
  cp .env.example .env
fi

# Generate an app key on first boot unless one was provided.
if [ -z "${APP_KEY:-}" ]; then
  php artisan key:generate --force
fi

# SQLite lives on the ephemeral disk for the free tier: fresh on every
# deploy, migrated on every boot.
mkdir -p database storage/framework/cache storage/framework/sessions \
         storage/framework/views storage/logs bootstrap/cache
touch database/database.sqlite

php artisan migrate --force

exec php artisan serve --host 0.0.0.0 --port "${PORT:-8080}"
