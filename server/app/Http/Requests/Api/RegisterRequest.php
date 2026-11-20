<?php

namespace App\Http\Requests\Api;

use App\Services\AuthService;
use App\Support\Passwords;
use Illuminate\Foundation\Http\FormRequest;

/**
 * The profile a player chooses after the Google sign-in.
 *
 * The MLBB ID is self-declared: it is stored as typed and never checked
 * against Moonton.
 */
class RegisterRequest extends FormRequest
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
            'username' => ['required', 'string', 'min:3', 'max:24', 'regex:'.AuthService::USERNAME_PATTERN],
            'mlbbId' => ['required', 'string', 'regex:'.AuthService::MLBB_ID_PATTERN],
            'password' => ['required', 'string', 'min:'.Passwords::MIN_LENGTH, 'max:'.Passwords::MAX_LENGTH],
        ];
    }

    /**
     * @return array<string, string>
     */
    public function messages(): array
    {
        return [
            'username.regex' => 'Use 3-24 letters, numbers, underscores, spaces or dots - it may not start or end with a space.',
            'mlbbId.regex' => 'The MLBB ID must be 4-20 digits.',
        ];
    }

    /**
     * @return array<string, string>
     */
    public function attributes(): array
    {
        return [
            'mlbbId' => 'MLBB ID',
        ];
    }
}
