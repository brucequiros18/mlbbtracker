<?php

namespace App\Http\Requests\Api;

use App\Services\AuthService;
use App\Support\Passwords;
use Illuminate\Foundation\Http\FormRequest;

/**
 * A profile edit, confirmed with the app password.
 *
 * The app password is not a sign-in credential - Google is.
 */
class UpdateProfileRequest extends FormRequest
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
            'username' => ['sometimes', 'nullable', 'string', 'min:3', 'max:24', 'regex:'.AuthService::USERNAME_PATTERN],
            'mlbbId' => ['sometimes', 'nullable', 'string', 'regex:'.AuthService::MLBB_ID_PATTERN],
            'currentPassword' => ['required', 'string', 'max:'.Passwords::MAX_LENGTH],
            'newPassword' => ['sometimes', 'nullable', 'string', 'min:'.Passwords::MIN_LENGTH, 'max:'.Passwords::MAX_LENGTH],
        ];
    }

    /**
     * @return array<string, string>
     */
    public function messages(): array
    {
        return [
            'username.regex' => 'Use 3-24 letters, numbers or underscores.',
            'mlbbId.regex' => 'The MLBB ID must be 4-20 digits.',
        ];
    }
}
