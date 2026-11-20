<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * Consented player connections.
 *
 * The provider JWT is stored server-side only; the app holds an opaque
 * session key whose SHA-256 hash is what appears in `session_hash`.
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::create('player_sessions', function (Blueprint $table): void {
            $table->id();
            $table->string('session_hash', 64)->unique();
            $table->text('provider_token');
            $table->string('role_id', 32);
            $table->string('zone_id', 16);
            $table->string('ign', 64)->nullable();
            $table->timestamps();
            $table->timestamp('last_seen_at');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('player_sessions');
    }
};
