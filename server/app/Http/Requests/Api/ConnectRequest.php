<?php

namespace App\Http\Requests\Api;

use Illuminate\Foundation\Http\FormRequest;

/**
 * Step 1: identify yourself. The values come from your in-game profile.
 */
class ConnectRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    /**
     * @return array<string, mixed>
     */
    public function rules(): array
    {
        return [
            'playerId' => ['required', 'string', 'max:32', 'regex:/^\d+$/'],
            'zoneId' => ['required', 'string', 'max:16', 'regex:/^\d+$/'],
        ];
    }

    /**
     * @return array<string, string>
     */
    public function attributes(): array
    {
        return [
            'playerId' => 'Player ID',
            'zoneId' => 'Zone ID',
        ];
    }
}
