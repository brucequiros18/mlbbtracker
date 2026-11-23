"""Generate docs/TECHNOLOGY_GLOSSARY.docx — every software, library, tool and
concept used in MLBB Tracker with its role and why it was chosen."""

import docx
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

DOC = docx.Document()

# ── style tweaks ──────────────────────────────────────────────────────────
style = DOC.styles['Normal']
style.font.name = 'Calibri'
style.font.size = Pt(11)
style.paragraph_format.space_after = Pt(6)
style.paragraph_format.line_spacing = 1.15

for level in (1, 2):
    h = DOC.styles[f'Heading {level}']
    h.font.name = 'Calibri'
    h.font.color.rgb = RGBColor(0x0B, 0x10, 0x20)
    if level == 1:
        h.font.size = Pt(20)
        h.font.bold = True
    else:
        h.font.size = Pt(14)
        h.font.bold = True

def add_bullet(text: str, level: int = 0) -> None:
    p = DOC.add_paragraph(text, style='List Bullet')
    p.paragraph_format.left_indent = Inches(0.25 + level * 0.25)

def add_mono(text: str) -> docx.text.run.Run:
    r = DOC.add_paragraph().add_run(text)
    r.font.name = 'Consolas'
    r.font.size = Pt(10)
    return r

# ── cover ────────────────────────────────────────────────────────────────
DOC.add_paragraph()
DOC.add_paragraph()
DOC.add_paragraph()
title = DOC.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run('MLBB Tracker — Technology Glossary')
run.font.size = Pt(26)
run.bold = True
run.font.color.rgb = RGBColor(0x2E, 0x7C, 0xD6)

sub = DOC.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = sub.add_run('Every software, library, tool and concept — what it is, what it does, and why we chose it')
run.font.size = Pt(12)
run.font.color.rgb = RGBColor(0x9A, 0xA8, 0xCB)

DOC.add_paragraph()
info = DOC.add_paragraph()
info.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = info.add_run('Prepared November 2026 · v0.12.0')
run.font.size = Pt(10)
run.font.color.rgb = RGBColor(0x5A, 0x67, 0x88)

DOC.add_page_break()

# ── table of contents ────────────────────────────────────────────────────
DOC.add_heading('Contents', level=1)
toc_items = [
    '1. Front-end Framework & Build',
    '2. State Management & Data Fetching',
    '3. UI & Styling',
    '4. Charts & Visualisation',
    '5. Back-end Framework & Language',
    '6. Database & ORM',
    '7. Authentication & Security',
    '8. External Data Providers',
    '9. Testing & Quality',
    '10. Packaging, Deployment & DevOps',
    '11. Mobile (Android)',
    '12. Documentation & Presentation',
    '13. Concept Glossary (Non-software)',
]
for item in toc_items:
    DOC.add_paragraph(item, style='List Bullet')
DOC.add_page_break()

# ── 1. Front-end Framework & Build ──────────────────────────────────────
DOC.add_heading('1. Front-end Framework & Build', level=1)

tech = [
    ('React 19',
     'The component library that builds the entire browser UI.',
     'Concurrent features, automatic batching, and the new compiler give '
     'better responsiveness with less boilerplate. It is the industry '
     'standard for rich SPAs and has first-class TypeScript support.'),
    ('TypeScript 5.6',
     'Static typing layer over JavaScript.',
     'Catches entire classes of bugs at compile time, makes refactoring '
     'safe, and documents the API contracts (props, query keys, envelope '
     'shapes) directly in the code.'),
    ('Vite 8',
     'Next-generation front-end build tool (dev server + production bundler).',
     'ESM-native, near-instant HMR, tiny config, and Rollup-based production '
     'builds. Replaces Webpack with a fraction of the complexity.'),
    ('ESLint / Oxlint',
     'Linters for JavaScript / TypeScript.',
     'Oxlint is Rust-fast for the common rules; ESLint handles the rest. '
     'Both run in CI and as pre-commit hooks.'),
    ('pnpm',
     'Fast, disk-efficient package manager.',
     'Content-addressable store means node_modules is a fraction of the '
     'size and installs are deterministic.'),
]

for name, what, why in tech:
    DOC.add_heading(name, level=2)
    p = DOC.add_paragraph()
    r = p.add_run('What it is: ')
    r.bold = True
    p.add_run(what)
    p = DOC.add_paragraph()
    r = p.add_run('Why we chose it: ')
    r.bold = True
    p.add_run(why)

# ── 2. State Management & Data Fetching ─────────────────────────────────
DOC.add_heading('2. State Management & Data Fetching', level=1)

tech = [
    ('TanStack Query (React Query) v5',
     'Server-state management: caching, deduping, background refetching, '
     'stale-while-revalidate, mutations with optimistic updates.',
     'Eliminates 90 % of custom data-fetching boilerplate. The devtools '
     'make cache state visible. Retries, deduping and selective invalidation '
     'are built-in and battle-tested.'),
    ('React Router v7',
     'Client-side routing with loaders, actions and nested routes.',
     'File-system-free, first-class TypeScript, and the new data APIs '
     'integrate with TanStack Query. The basename option is what lets the '
     'same build serve both the single-origin and GitHub Pages deployments.'),
    ('useFavourites (localStorage)',
     'Tiny hook that persists the watchlist slugs in the browser.',
     'No server round-trip, zero latency, and the list survives reloads. '
     'It is intentionally local-only — there is no server-side bookmark.'),
]

for name, what, why in tech:
    DOC.add_heading(name, level=2)
    p = DOC.add_paragraph()
    r = p.add_run('What it is: ')
    r.bold = True
    p.add_run(what)
    p = DOC.add_paragraph()
    r = p.add_run('Why we chose it: ')
    r.bold = True
    p.add_run(why)

# ── 3. UI & Styling ─────────────────────────────────────────────────────
DOC.add_heading('3. UI & Styling', level=1)

tech = [
    ('Tailwind CSS v4',
     'Utility-first CSS framework — styles are applied by composing '
     'utility classes in the markup.',
     'No context-switching to CSS files, dead-code elimination by design, '
     'and the v4 engine is Lightning CSS (Rust) — sub-millisecond builds. '
     'The design tokens (colors, spacing, radii) are defined once in '
     'CSS variables and consumed everywhere.'),
    ('CSS Variables (Custom Properties)',
     'The single source of truth for the "Land of Dawn" theme: colors, '
     'radii, shadows, font stacks.',
     'Changing a token (e.g. --accent) updates the whole app instantly; '
     'light/dark mode is a one-class toggle on <html>. No recompile needed.'),
    ('Rajdhani / Inter (Google Fonts)',
     'Rajdhani for headlines (esports, geometric), Inter for body text.',
     'Both are variable fonts served from fonts.googleapis.com with '
     'font-display: swap — no layout shift, sub-50 KB each.'),
    ('Inline SVG Icons (icons.tsx)',
     'Every icon is a tiny React component returning an <svg>.',
     'Zero extra requests, tree-shakable, styleable with currentColor, '
     'and accessible by default (aria-hidden + parent labels).'),
]

for name, what, why in tech:
    DOC.add_heading(name, level=2)
    p = DOC.add_paragraph()
    r = p.add_run('What it is: ')
    r.bold = True
    p.add_run(what)
    p = DOC.add_paragraph()
    r = p.add_run('Why we chose it: ')
    r.bold = True
    p.add_run(why)

# ── 4. Charts & Visualisation ──────────────────────────────────────────
DOC.add_heading('4. Charts & Visualisation', level=1)

tech = [
    ('Recharts',
     'Declarative React charting library built on D3 primitives.',
     'React-native (no refs/DOM gymnastics), responsive out of the box, '
     'composable (LineChart, AreaChart, BarChart, Tooltip, Legend, …), '
     'and the bundle is reasonable (~120 KB gzipped with the few components '
     'we import).'),
    ('Custom sparklines (TierBadge, TrendDelta)',
     'Tiny inline SVG trends drawn without a charting lib.',
     'Micro-optimised for the watchlist and tier list — a few path '
     'commands, zero dependencies, and they scale with the text.'),
]

for name, what, why in tech:
    DOC.add_heading(name, level=2)
    p = DOC.add_paragraph()
    r = p.add_run('What it is: ')
    r.bold = True
    p.add_run(what)
    p = DOC.add_paragraph()
    r = p.add_run('Why we chose it: ')
    r.bold = True
    p.add_run(why)

# ── 5. Back-end Framework & Language ───────────────────────────────────
DOC.add_heading('5. Back-end Framework & Language', level=1)

tech = [
    ('PHP 8.4',
     'The language runtime for the API.',
     'JIT, typed properties, enums, readonly classes, and the new '
     'random_extension make PHP competitive with Node/Go for API workloads. '
     'Laravel 13 targets 8.4+.'),
    ('Laravel 13',
     'Full-stack PHP framework — routing, DI container, Eloquent ORM, '
     'migrations, queues, scheduler, testing helpers, and the single-origin '
     'SPA serving pattern built-in.',
     'Convention over configuration, first-class testing (PHPUnit + Pest), '
     'excellent docs, and the ecosystem (Laravel Boost, Octane, Pulse) '
     'means we don\'t reinvent auth, rate-limiting, or caching.'),
    ('Laravel Octane (RoadRunner / Swoole) — optional',
     'High-performance application server that keeps the bootstrapped '
     'application in memory.',
     'Used in production (Render) for 10× throughput vs php-fpm; not '
     'required for local dev where php artisan serve is fine.'),
]

for name, what, why in tech:
    DOC.add_heading(name, level=2)
    p = DOC.add_paragraph()
    r = p.add_run('What it is: ')
    r.bold = True
    p.add_run(what)
    p = DOC.add_paragraph()
    r = p.add_run('Why we chose it: ')
    r.bold = True
    p.add_run(why)

# ── 6. Database & ORM ──────────────────────────────────────────────────
DOC.add_heading('6. Database & ORM', level=1)

tech = [
    ('SQLite (dev) / PostgreSQL (prod)',
     'Relational database — file-based for zero-config local dev, '
     'Postgres on Render for production.',
     'Same SQL dialect, same migrations. SQLite means a new contributor '
     'runs one command and has a working DB; Postgres scales.'),
    ('Eloquent ORM',
     'Laravel\'s Active-Record implementation — fluent query builder, '
     'relationships, accessors/mutators, scopes, and eager loading.',
     'Expressive, type-hinted (via Laravel IDE Helper), and the migration '
     'system keeps schema changes versioned and reviewable.'),
    ('Migrations',
     'Version-controlled schema changes (PHP classes with up()/down()).',
     'Every schema change is code-reviewed, reversible, and runs '
     'automatically on deploy (php artisan migrate --force).'),
]

for name, what, why in tech:
    DOC.add_heading(name, level=2)
    p = DOC.add_paragraph()
    r = p.add_run('What it is: ')
    r.bold = True
    p.add_run(what)
    p = DOC.add_paragraph()
    r = p.add_run('Why we chose it: ')
    r.bold = True
    p.add_run(why)

# ── 7. Authentication & Security ───────────────────────────────────────
DOC.add_heading('7. Authentication & Security', level=1)

tech = [
    ('Firebase Authentication (Email/Password + Google)',
     'Managed identity provider — sign-up, sign-in, password reset, '
     'email verification, and Google OAuth.',
     'We only verify the returned RS256 ID token on our server; '
     'we never store the token. No password hashing, no session DB on '
     'Firebase\'s side, and MFA / breach protection come for free.'),
    ('Google Identity Services (GIS)',
     'The official "Sign in with Google" button rendered by Google.',
     'One line of JS, CSP-compatible, and the credential is an ID token '
     'we verify exactly like a Firebase token.'),
    ('Custom RS256 Verification (App\\Support\\FirebaseTokenVerifier, GoogleTokenVerifier)',
     'Server-side verification of the JWT signature against the provider\'s '
     'published JWKS / X.509 certs, plus issuer, audience, expiry, '
     'and email_verified checks.',
     'The browser never decides who the user is — the API does. Tokens are '
     'never stored; only the stable sub claim becomes the account key. '
     'Covered by 27 offline crypto tests (forged sig, wrong issuer, expiry, '
     'key rotation, cert outage).'),
    ('Argon2id (PHP password_hash)',
     'Memory-hard KDF for the app password (profile-edit confirmation).',
     'Recommended by OWASP, built into PHP 8.4, and the only hashing '
     'algorithm we use — no Bcrypt, no scrypt.'),
    ('Content-Security-Policy (strict)',
     'Helmet-like header built in App\\Support\\Csp — connect-src '
     'explicitly allow-lists identitytoolkit.googleapis.com, '
     'securetoken.googleapis.com, and accounts.google.com; script-src '
     'is self + nonce; no unsafe-inline.',
     'Prevents XSS, data exfiltration, and the "Could not reach Firebase" '
     'bug we fixed when the policy accidentally blocked Firebase\'s own '
     'endpoints. Regression tests pin the CSP.'),
    ('Rate Limiting (Laravel throttle middleware)',
     'Per-route, per-IP limits on auth and provider endpoints.',
     'Prevents credential stuffing and provider abuse without a separate '
     'WAF.'),
]

for name, what, why in tech:
    DOC.add_heading(name, level=2)
    p = DOC.add_paragraph()
    r = p.add_run('What it is: ')
    r.bold = True
    p.add_run(what)
    p = DOC.add_paragraph()
    r = p.add_run('Why we chose it: ')
    r.bold = True
    p.add_run(why)

# ── 8. External Data Providers ─────────────────────────────────────────
DOC.add_heading('8. External Data Providers', level=1)

tech = [
    ('Rone Arena API',
     'Community-run endpoint: hero win/ban/pick rates by rank bracket '
     'and time window, plus player profile / match history (consented).',
     'The only live source for ranked meta rates. We cache responses, '
     'normalize hero names, and attribute every payload with meta.sources.'),
    ('MLBBDex (CC BY-SA 4.0)',
     'Community wiki data: hero roster (133), roles, lanes, base stats, '
     'tier assignments, and skill metadata.',
     'The canonical roster — we merge Rone\'s rates against MLBBDex\'s '
     'identities so every hero has a stable slug, icon, and tier. '
     'License requires attribution, which we include in every API response.'),
]

for name, what, why in tech:
    DOC.add_heading(name, level=2)
    p = DOC.add_paragraph()
    r = p.add_run('What it is: ')
    r.bold = True
    p.add_run(what)
    p = DOC.add_paragraph()
    r = p.add_run('Why we chose it: ')
    r.bold = True
    p.add_run(why)

# ── 9. Testing & Quality ───────────────────────────────────────────────
DOC.add_heading('9. Testing & Quality', level=1)

tech = [
    ('PHPUnit 11',
     'Unit / feature test runner for PHP.',
     '60 tests, 274 assertions, fully offline. Runs in ~2 s. Covers auth '
     'flows, token verifiers, CSP headers, provider health, and the API '
     'contract envelope.'),
    ('Pest (optional, not yet adopted)',
     'Expressive wrapper over PHPUnit — not used yet but on the radar.',
     'Would give more readable test output and built-in parallelization; '
     'evaluating for a future migration.'),
    ('Laravel Pint',
     'Opinionated code formatter (PHP-CS-Fixer based) with the Laravel preset.',
     'Runs in CI and as a pre-commit hook; guarantees consistent style '
     'without bikeshedding.'),
    ('TanStack Query DevTools (dev only)',
     'Browser panel showing cache state, query keys, stale status, and '
     'manual refetch/invalidate.',
     'Essential for debugging server-state bugs without console.log spam.'),
    ('Playwright (Python)',
     'End-to-end browser automation for the demo video and the Pages QA '
     'suite (12 checks: landing, mobile, SPA root, deep link, 404 fallback).',
     'Runs headless Chromium / Edge; no flaky Selenium.'),
]

for name, what, why in tech:
    DOC.add_heading(name, level=2)
    p = DOC.add_paragraph()
    r = p.add_run('What it is: ')
    r.bold = True
    p.add_run(what)
    p = DOC.add_paragraph()
    r = p.add_run('Why we chose it: ')
    r.bold = True
    p.add_run(why)

# ── 10. Packaging, Deployment & DevOps ────────────────────────────────
DOC.add_heading('10. Packaging, Deployment & DevOps', level=1)

tech = [
    ('GitHub Actions',
     'CI/CD pipelines — lint, test, build, and publish on every push.',
     'Native, free for public repos, matrix builds for PHP/Node versions, '
     'and the gh-pages deploy is a single workflow step.'),
    ('GitHub Pages (static hosting)',
     'Serves the download website (site/) at the root and the React SPA '
     'demo under /mlbbtracker/app/.',
     'Free HTTPS, custom domain ready, and the SPA-fallback trick (404.html '
     'redirect) makes client-side routing work without a server.'),
    ('Render (cloud PaaS)',
     'Managed Docker deployment — multi-stage Dockerfile builds the Vite '
     'bundle, installs Composer deps, and runs Octane.',
     'Free tier for hobby projects, auto-deploys from main, health checks, '
     'and zero-config TLS.'),
    ('Docker (multi-stage)',
     'Build stage: Node 20 + pnpm → Vite build. Runtime stage: PHP 8.4 + '
     'Composer + Octane binary.',
     'Produces a ~120 MB image that starts in <2 s. Same image runs locally '
     'and on Render.'),
    ('deploy_pages.ps1',
     'PowerShell script that builds with VITE_ROUTER_BASENAME=/mlbbtracker/app/, '
     'assembles the landing + SPA + 404.html tree, and force-pushes gh-pages.',
     'One command publishes both sites. Local QA via build/pages_qa.py '
     'mirrors the exact Pages tree.'),
    ('package_windows.ps1',
     'Bundles PHP 8.4.28 (non-thread-safe), the Laravel app (vendor + '
     'public/app), an empty SQLite file, and START-MLBB-TRACKER.bat into '
     'a 50 MB zip.',
     'Double-click → migrate → serve → browser opens at 127.0.0.1:8000. '
     'No installs, no admin, no PATH pollution. SHA-256 published on the '
     'download page.'),
]

for name, what, why in tech:
    DOC.add_heading(name, level=2)
    p = DOC.add_paragraph()
    r = p.add_run('What it is: ')
    r.bold = True
    p.add_run(what)
    p = DOC.add_paragraph()
    r = p.add_run('Why we chose it: ')
    r.bold = True
    p.add_run(why)

# ── 11. Mobile (Android) ───────────────────────────────────────────────
DOC.add_heading('11. Mobile (Android)', level=1)

tech = [
    ('Flutter 3.24 + Dart 3.5',
     'Cross-platform UI toolkit — single codebase, native ARM compilation.',
     'Material 3, hot reload, and the same Dart logic can be reused for '
     'a future desktop build.'),
    ('Riverpod 2.5',
     'Compile-safe state management (providers, notifiers, families).',
     'No BuildContext, testable in pure Dart, and the compiler catches '
     'missing providers.'),
    ('Dio 5.7',
     'Powerful HTTP client with interceptors, retries, and form-data.',
     'Talks to the same /api/v1 the web app uses.'),
    ('FL Chart 0.69',
     'Flutter-native line/bar/pie charts for the mobile dashboard.',
     'No platform channels, small bundle, and the API mirrors Recharts '
     'closely enough to share the same visual language.'),
    ('package_apk.ps1 / package_windows.ps1',
     'Same philosophy as the Windows packager — one script, signed APK, '
     'SHA-256, and GitHub Release upload.',
     'Consistent release process across platforms.'),
]

for name, what, why in tech:
    DOC.add_heading(name, level=2)
    p = DOC.add_paragraph()
    r = p.add_run('What it is: ')
    r.bold = True
    p.add_run(what)
    p = DOC.add_paragraph()
    r = p.add_run('Why we chose it: ')
    r.bold = True
    p.add_run(why)

# ── 12. Documentation & Presentation ───────────────────────────────────
DOC.add_heading('12. Documentation & Presentation', level=1)

tech = [
    ('Markdown (README, CHANGELOG, DEPLOYMENT, API_DOCUMENTATION, TESTING_REPORT)',
     'Plain-text, diff-friendly, renderable everywhere.',
     'Source of truth for humans and CI. CHANGELOG follows Keep a Changelog.'),
    ('python-docx',
     'Generates PROJECT_EXPLANATION_SCRIPT.docx and TECHNOLOGY_GLOSSARY.docx '
     'from structured Python data.',
     'Reproducible, version-controlled, and the script is the documentation.'),
    ('pptxgenjs (Node) + expand_deck.py',
     'Generates the 18-slide MLBB-Tracker-Presentation.pptx with live API '
     'samples, real charts, and the Land of Dawn palette.',
     'Data-driven: when realdata.json updates, the deck regenerates with '
     'current numbers.'),
    ('edge-tts + Playwright + ffmpeg',
     'Free local narration (GuyNeural), screen capture, caption overlay, '
     'and final MP4 assembly for the demo video.',
     'Zero cloud cost, fully offline, and the script is the video.'),
]

for name, what, why in tech:
    DOC.add_heading(name, level=2)
    p = DOC.add_paragraph()
    r = p.add_run('What it is: ')
    r.bold = True
    p.add_run(what)
    p = DOC.add_paragraph()
    r = p.add_run('Why we chose it: ')
    r.bold = True
    p.add_run(why)

# ── 13. Concept Glossary (Non-software) ────────────────────────────────
DOC.add_heading('13. Concept Glossary (Non-software)', level=1)

concepts = [
    ('Single-Origin Architecture',
     'The React build is copied into Laravel\'s public/app/ directory; '
     'one server serves both the SPA (/) and the API (/api/v1). No CORS, '
     'no preflight, no separate frontend hosting.'),
    ('{data, meta} Envelope',
     'Every JSON response is { "data": ..., "meta": { generatedAt, cached, '
     'sources[], note? } }. Lists and items share the same shape; errors '
     'are { "status":"error", "code":"...", "message":"...", "details"?, '
     '"timestamp":"..." }. Stable across FastAPI → Laravel migration.'),
    ('Attribution-First Data',
     'Every payload names its upstream providers in meta.sources. Rates '
     'are published exactly as reported; missing data is shown as missing, '
     'never invented.'),
    ('Self-Declared MLBB ID',
     'The player types their in-game ID; it is stored verbatim and flagged '
     'mlbbIdVerified: false everywhere. We never verify it against Moonton.'),
    ('App Password (Argon2id)',
     'A second password chosen at profile setup. It only confirms profile '
     'edits — it is never a login credential, and the Firebase/Google token '
     'remains the sole sign-in method.'),
    ('Opaque Session Tokens',
     'On successful sign-in the API returns a random opaque token. Only its '
     'SHA-256 digest is stored; the raw token is never persisted. 30-day '
     'sliding expiry.'),
    ('Consented Player Connect',
     'The player requests a one-time code in the app, receives it in their '
     'in-game mailbox, and submits it. The server then polls Rone Arena for '
     'that player\'s profile/stats/matches. No game password ever enters '
     'our system.'),
    ('Snapshot History (hero_snapshots)',
     'A daily Artisan command fetches the 7-day rankings and writes one row '
     'per hero (win/ban/pick). This is the app\'s own recorded history, '
     'separate from provider trends.'),
    ('Tier List (S+ → C)',
     'Wiki-backed tier boundaries applied to the live win rate. The tier '
     'badge is computed server-side and included in the API response.'),
    ('Strict CSP (Content-Security-Policy)',
     'connect-src explicitly allow-lists identitytoolkit.googleapis.com, '
     'securetoken.googleapis.com, and accounts.google.com. script-src '
     'uses nonces. The download page has an even stricter policy '
     '(connect-src \'self\' only).'),
    ('GitHub Pages SPA-Fallback',
     'Pages serves 404.html for unknown paths. Our 404.html is the SPA index '
     'plus a script that folds /mlbbtracker/<page> → /mlbbtracker/app/<page> '
     'so React Router\'s basename matches and deep links work.'),
    ('Windows Self-Contained Package',
     'ZIP with bundled PHP 8.4.28 (NTS), vendor/, public/app/, empty SQLite, '
     'and START-MLBB-TRACKER.bat. No PATH changes, no admin, no installs.'),
    ('Semantic Versioning + Keep a Changelog',
     'v0.12.0 = major.minor.patch; CHANGELOG.md entries map 1:1 to tags.'),
]

for term, definition in concepts:
    DOC.add_heading(term, level=2)
    DOC.add_paragraph(definition)

# ── save ─────────────────────────────────────────────────────────────────
OUT = r"D:\projs\project1\docs\TECHNOLOGY_GLOSSARY.docx"
DOC.save(OUT)
print(f"Saved {OUT}")