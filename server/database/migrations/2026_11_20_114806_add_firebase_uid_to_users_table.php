<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * Firebase accounts sign in with an email + password handled by Firebase
 * Authentication. The stable identity key is the Firebase UID (`sub` claim of
 * the verified ID token) - never the email. Google accounts keep using
 * `google_sub`; a row has whichever credential created it.
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::table('users', function (Blueprint $table): void {
            // A row carries whichever credential created it, so neither
            // subject column may require the other.
            $table->string('google_sub', 64)->nullable()->change();
            $table->string('firebase_uid', 128)->nullable()->unique()->after('google_sub');
        });
    }

    public function down(): void
    {
        Schema::table('users', function (Blueprint $table): void {
            $table->string('google_sub', 64)->change();
            $table->dropColumn('firebase_uid');
        });
    }
};
