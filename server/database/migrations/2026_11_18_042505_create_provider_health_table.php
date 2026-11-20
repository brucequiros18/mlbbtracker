<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * One observed provider call: reachability, latency and status.
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::create('provider_health', function (Blueprint $table): void {
            $table->id();
            $table->string('provider', 64)->index();
            $table->string('endpoint', 160);
            $table->string('status', 16);
            $table->integer('status_code')->nullable();
            $table->integer('latency_ms')->nullable();
            $table->string('error_code', 48)->nullable();
            $table->timestamp('checked_at');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('provider_health');
    }
};
