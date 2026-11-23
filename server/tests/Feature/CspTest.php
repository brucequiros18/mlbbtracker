<?php

namespace Tests\Feature;

use Tests\TestCase;

class CspTest extends TestCase
{
    /**
     * The SPA's Content-Security-Policy must allow the endpoints Firebase
     * Authentication posts to. Without them the browser blocks the request
     * and the SDK reports auth/network-request-failed ("Could not reach
     * Firebase"), which looks like a connection problem but is our own
     * policy refusing the connection.
     */
    public function test_spa_content_security_policy_allows_firebase_authentication(): void
    {
        $response = $this->get('/');

        $response->assertStatus(200);

        $csp = $response->headers->get('Content-Security-Policy');

        $this->assertNotNull($csp, 'The SPA response must carry a Content-Security-Policy header.');
        $this->assertStringContainsString('https://identitytoolkit.googleapis.com', $csp);
        $this->assertStringContainsString('https://securetoken.googleapis.com', $csp);
    }

    /** Google sign-in endpoints stay allowed alongside Firebase. */
    public function test_spa_content_security_policy_keeps_google_sign_in(): void
    {
        $csp = $this->get('/')->headers->get('Content-Security-Policy');

        $this->assertNotNull($csp);
        $this->assertStringContainsString('https://accounts.google.com', $csp);
        $this->assertStringContainsString("connect-src 'self'", $csp);
    }

    /** The download page stays strict: no third-party connections at all. */
    public function test_download_page_policy_remains_closed(): void
    {
        $csp = $this->get('/download')->headers->get('Content-Security-Policy');

        $this->assertNotNull($csp);
        $this->assertStringContainsString("connect-src 'self'", $csp);
        $this->assertStringNotContainsString('identitytoolkit', $csp);
    }
}
