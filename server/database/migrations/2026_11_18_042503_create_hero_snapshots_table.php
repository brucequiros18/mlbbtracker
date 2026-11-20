<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * A daily observation of a hero's rank-window statistics.
 *
 * Rows are written whenever the server fetches the 7-day rankings from the
 * live provider and no snapshot exists yet for (hero, window, day).
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::create('hero_snapshots', function (Blueprint $table): void {
            $table->id();
            $table->integer('hero_id')->index();
            $table->string('hero_name', 64);
            $table->integer('days')->default(7);
            $table->date('captured_on')->index();
            $table->float('win_rate');
            $table->float('ban_rate');
            $table->float('pick_rate');
            $table->string('tier', 16)->nullable();
            $table->integer('rank_position')->nullable();
            $table->timestamps();
            $table->unique(['hero_id', 'days', 'captured_on'], 'uq_hero_day_window');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('hero_snapshots');
    }
};
