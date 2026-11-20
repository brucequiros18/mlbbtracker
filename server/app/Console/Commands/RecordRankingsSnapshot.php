<?php

namespace App\Console\Commands;

use App\Models\HeroSnapshot;
use App\Services\HeroService;
use Illuminate\Console\Attributes\Description;
use Illuminate\Console\Attributes\Signature;
use Illuminate\Console\Command;
use Throwable;

/**
 * Record a snapshot of the live 7-day rankings into the local database.
 *
 * Intended for a scheduled task (Task Scheduler / cron) so history accumulates
 * even when nobody is using the app. Safe to re-run: one row per hero per UTC
 * day (HeroService::rankings() skips heroes already captured today).
 */
#[Signature('mlbb:record-snapshot {--days=7 : Rankings window (canonical: 7)}')]
#[Description('Record one daily snapshot of the live 7-day rankings (idempotent per UTC day).')]
class RecordRankingsSnapshot extends Command
{
    /**
     * Execute the console command.
     */
    public function handle(HeroService $heroes): int
    {
        $days = (int) $this->option('days');

        try {
            $rows = $heroes->rankings($days, 'all', 'win_rate');
        } catch (Throwable $exception) {
            $this->error('Rankings fetch failed: '.$exception->getMessage());

            return 1;
        }

        $recorded = HeroSnapshot::query()
            ->where('days', $days)
            ->whereDate('captured_on', now()->utc()->toDateString())
            ->count();

        $this->info('provider rows: '.count($rows)."; snapshot rows stored today: {$recorded}");

        return 0;
    }
}
