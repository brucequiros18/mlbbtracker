<?php

namespace App\Http\Requests\Api;

/**
 * Step 2: the one-time code delivered to your in-game mailbox.
 */
class ConnectVerifyRequest extends ConnectRequest
{
    /**
     * @return array<string, mixed>
     */
    public function rules(): array
    {
        return array_merge(parent::rules(), [
            'code' => ['required', 'string', 'min:4', 'max:8', 'regex:/^\d+$/'],
        ]);
    }
}
