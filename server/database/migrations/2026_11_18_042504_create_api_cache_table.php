<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * Persistent provider-response cache (survives a server restart).
 *
 * The cache store is the hot tier; this table is the cold tier that keeps a
 * restart from re-fetching the full hero catalog from upstream.
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::create('api_cache', function (Blueprint $table): void {
            $table->id();
            $table->string('cache_key', 160)->unique();
            $table->string('provider', 64);
            $table->json('payload');
            $table->timestamp('expires_at');
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('api_cache');
    }
};
