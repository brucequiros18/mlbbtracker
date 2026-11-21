# MLBB Tracker - Laravel API + built React SPA in one container.
# Built by Render (render.yaml) or any Docker host.

# ── Stage 1: build the React bundle ────────────────────────────────────
FROM node:22-alpine AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ .
RUN npm run build

# ── Stage 2: PHP runtime ───────────────────────────────────────────────
FROM php:8.4-cli

RUN apt-get update \
    && apt-get install -y --no-install-recommends git unzip libsqlite3-dev libpq-dev \
    && docker-php-ext-install pdo pdo_sqlite pdo_pgsql \
    && rm -rf /var/lib/apt/lists/*

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

WORKDIR /var/www
COPY server/composer.json server/composer.lock ./
RUN composer install --no-dev --no-interaction --prefer-dist --no-scripts

COPY server/ .
COPY --from=web /web/dist /var/www/public/app

RUN chmod -R ug+rwX storage bootstrap/cache database

COPY server/docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080
ENTRYPOINT ["/entrypoint.sh"]
