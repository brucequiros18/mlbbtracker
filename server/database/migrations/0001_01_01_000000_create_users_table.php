<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * App accounts. Google is the only credential.
 *
 * `google_sub` is the stable subject of a verified Google ID token, so it is
 * the identity key - never the email. `username`, `mlbb_id` and
 * `password_hash` are app-only profile data: the MLBB ID is self-declared and
 * never verified against Moonton, and the password is an app-only hash that
 * is never a sign-in method.
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::create('users', function (Blueprint $table): void {
            $table->id();
            $table->string('google_sub', 64)->unique();
            $table->string('email', 320);
            $table->boolean('email_verified')->default(false);
            $table->string('google_name', 120)->nullable();
            $table->text('picture_url')->nullable();
            $table->string('username', 24)->unique()->nullable();
            $table->string('mlbb_id', 32)->nullable();
            $table->string('password_hash', 255)->nullable();
            $table->timestamps();
            $table->timestamp('last_login_at')->nullable();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('users');
    }
};
