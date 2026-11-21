"""Generate docs/PROJECT_EXPLANATION_SCRIPT.docx.

A presenter-ready script for explaining the MLBB Tracker system: what it is,
how it is built, how data flows, how security works, and a prepared
question-and-answer section for technical panels.

Run from the repository root::

    python scripts/generate_project_doc.py

Requires python-docx (pip install python-docx).
"""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

OUT = Path(__file__).resolve().parent.parent / "docs" / "PROJECT_EXPLANATION_SCRIPT.docx"

INK = RGBColor(0x1F, 0x1E, 0x1D)
ACCENT = RGBColor(0x1E, 0x62, 0xD0)
MUTED = RGBColor(0x57, 0x56, 0x4F)


def set_base_style(document: Document) -> None:
    style = document.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.font.color.rgb = INK


def title(document: Document, text: str, subtitle: str) -> None:
    heading = document.add_paragraph()
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = heading.add_run(text)
    run.font.size = Pt(28)
    run.font.bold = True
    run.font.color.rgb = ACCENT

    sub = document.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = sub.add_run(subtitle)
    sub_run.font.size = Pt(13)
    sub_run.font.color.rgb = MUTED
    document.add_paragraph()


def h1(document: Document, text: str) -> None:
    run = document.add_heading(text, level=1)
    for part in run.runs:
        part.font.color.rgb = ACCENT


def h2(document: Document, text: str) -> None:
    run = document.add_heading(text, level=2)
    for part in run.runs:
        part.font.color.rgb = INK


def body(document: Document, text: str, bold_prefix: str | None = None) -> None:
    paragraph = document.add_paragraph()
    if bold_prefix:
        bold = paragraph.add_run(bold_prefix + " ")
        bold.bold = True
    paragraph.add_run(text)


def bullets(document: Document, items: list[str]) -> None:
    for item in items:
        document.add_paragraph(item, style="List Bullet")


def qa(document: Document, question: str, answer: str) -> None:
    q = document.add_paragraph()
    q_run = q.add_run("Q: " + question)
    q_run.bold = True
    a = document.add_paragraph()
    a.add_run("A: " + answer)
    document.add_paragraph()


def build() -> None:
    document = Document()
    set_base_style(document)

    title(
        document,
        "MLBB Tracker",
        "Project Explanation & Defense Script — React + Vite web app, Laravel API, "
        "Firebase accounts, MLBB-inspired design. Prepared November 2026.",
    )

    # ── 1. The pitch ─────────────────────────────────────────────────────
    h1(document, "1. The 30-second pitch")
    body(
        document,
        "MLBB Tracker is a full-stack analytics platform for Mobile Legends: Bang Bang. "
        "It turns two live community data providers into a clean, honest analytics "
        "experience: a 133-hero roster, win/ban/pick meta rankings with a tier list, "
        "7-day trend charts, recorded daily history, hero head-to-head comparison, a "
        "personal watchlist, and Mobile Legends Professional League standings with "
        "verified grand-final results. Accounts run on Firebase email-and-password "
        "sign-in verified on our own Laravel server, and the whole app installs as a "
        "PWA. Every number in the UI traces to a provider observation or a "
        "source-linked esports result — the system never fabricates data.",
    )

    # ── 2. Architecture ──────────────────────────────────────────────────
    h1(document, "2. System architecture")
    body(
        document,
        "Three tiers. The client tier is a React 19 single-page app built with Vite and "
        "TypeScript, styled with Tailwind v4, fetching through TanStack Query and "
        "charting with Recharts. The server tier is a Laravel 13 (PHP 8.4) REST API "
        "that owns all business logic: identity verification, accounts and sessions, "
        "provider merging, caching and snapshot recording. The data tier is SQLite in "
        "development and Postgres-ready in production, plus two external providers "
        "(Rone Arena and MLBBDex).",
    )
    body(
        document,
        "The defining architectural choice is the single origin: the built React bundle "
        "is copied into Laravel's public directory, so the API and the app ship from "
        "one URL. That removes CORS entirely, makes cookies and service-worker scope "
        "trivial, and turns the deploy into one directory.",
        bold_prefix="Single origin.",
    )
    body(
        document,
        "The Laravel side reads two different providers and merges them: Rone Arena "
        "supplies hero identity, portraits, relationships, rankings and esports; MLBBDex "
        "supplies roles, lanes, skills and wiki-backed tiers. A HeroService normalizes "
        "both into one camelCase JSON contract with per-data-type TTL caching — six "
        "hours for the catalog, one hour for rankings — backed by a database cache "
        "table so restarts do not stampede the providers.",
        bold_prefix="Provider aggregation.",
    )

    # ── 3. Data flow ─────────────────────────────────────────────────────
    h1(document, "3. How data flows (worked example: the tier list)")
    bullets(
        document,
        [
            "The browser asks GET /api/v1/heroes/rankings?days=7&rank=all&sort=win_rate.",
            "Laravel checks the fast cache, then the database cache table; on a miss it "
            "fetches live rankings from Rone Arena and hero tiers from MLBBDex.",
            "HeroService merges the two: every provider row is matched to the roster, "
            "tier badges attached, rates rounded, results sorted and cached.",
            "While serving a 7-day window the service also writes one snapshot row per "
            "hero per UTC day into hero_snapshots — idempotent, so retries never "
            "duplicate. A scheduled Artisan command (mlbb:record-snapshot) does the same "
            "when nobody is browsing, which is how the recorded-history charts grow.",
            "React receives the {data, meta} envelope; TanStack Query caches it for five "
            "minutes, and the tier-list view groups heroes by tier with theme-colored "
            "badges. The meta envelope carries generatedAt, cached, count and source "
            "attribution, so the UI can always say where a number came from.",
        ],
    )

    # ── 4. Database ──────────────────────────────────────────────────────
    h1(document, "4. Database design")
    bullets(
        document,
        [
            "users — one row per account. Identity is the Firebase UID or the Google "
            "sub of a verified ID token, never the email. username is unique "
            "case-insensitively; mlbb_id is self-declared; password_hash is Argon2id.",
            "user_sessions — opaque bearer tokens; only the SHA-256 digest is stored, "
            "with a 30-day sliding expiry.",
            "player_sessions — the consented in-game account link (same digest pattern).",
            "hero_snapshots — the daily observations that power recorded history.",
            "api_cache — the durable provider cache behind the TTLs.",
            "provider_health — event log of upstream failures and recoveries.",
        ],
    )

    # ── 5. Authentication ────────────────────────────────────────────────
    h1(document, "5. Authentication, step by step")
    bullets(
        document,
        [
            "Sign-up: the Firebase JS SDK creates the account (email + password) and "
            "returns an ID token.",
            "The browser POSTs that token to POST /api/v1/auth/firebase.",
            "Laravel's FirebaseTokenVerifier verifies it locally: RS256 signature "
            "against Firebase's published X509 certificates (fetched once, cached one "
            "hour, refetched on an unknown key id), issuer "
            "https://securetoken.google.com/<project>, audience equal to our project id, "
            "expiry and issued-at checks, a non-empty sub, and a non-empty email.",
            "Only then is the sub trusted: the user row is created or reused, and an "
            "opaque session token is issued and returned.",
            "The React app stores the session token and calls it with a Bearer header. "
            "The password chosen at sign-up never reaches our database — a separate "
            "Argon2id 'app password' confirms profile edits only.",
            "Google sign-in follows the identical pattern through GoogleTokenVerifier, "
            "against Google's JWKS. Both verifiers are covered by 27 offline tests "
            "that sign real RS256 tokens and assert every rejection path.",
        ],
    )

    # ── 6. Features walkthrough ──────────────────────────────────────────
    h1(document, "6. Feature walkthrough (demo script)")
    h2(document, "6.1 Rankings + tier list")
    body(
        document,
        "Open the Ranks tab. The default view groups the live rankings into a tier "
        "list: S+ in gold, S in ember, A in purple, B in blue, C in slate — colors "
        "that adapt to both themes. Filters change the rank bracket (Epic through "
        "Mythical Glory) and the time window. Toggle to Table for sortable columns.",
    )
    h2(document, "6.2 Watchlist (Saved)")
    body(
        document,
        "Bookmark heroes anywhere in the app. The Saved tab becomes a watchlist: a "
        "summary strip (count, average win rate versus the meta average, how many sit "
        "in S+/S), per-hero tier badge, win-rate rank position and 7-day movement "
        "chips. Sort by movement to see which of your heroes is climbing today.",
    )
    h2(document, "6.3 Comparison")
    body(
        document,
        "Tick two or three watchlist heroes and press Compare. The comparison view "
        "puts them side by side — tier, roles, win/ban/pick with the best value "
        "highlighted, strong/weak matchups — and overlays their 7-day win-rate trends "
        "on one chart. The selection lives in the URL, so any comparison is shareable.",
    )
    h2(document, "6.4 Esports")
    body(
        document,
        "The Esports tab shows the M7 World Championship result (Aurora Gaming PH "
        "swept Alter Ego 4-0 in Jakarta, January 2026) and each league's latest grand "
        "final: Bigetron by Vitality's back-to-back MPL Indonesia titles, Team Liquid "
        "PH's 4-0 sweep in the Philippines, Selangor Red Giants' six-peat in Malaysia "
        "and Vigor Apex's undefeated run in Cambodia. Every result links its source "
        "and carries a verified-on date; match-by-match bracket logs are not "
        "published by the provider, and the UI says so instead of inventing them.",
    )
    h2(document, "6.5 PWA + download page")
    body(
        document,
        "Install the app from the address bar or /download. A service worker caches "
        "the shell only — API responses are never cached, so offline you get honest "
        "error states, not stale numbers pretending to be live. /download serves the "
        "Android APK with version, size and SHA-256.",
    )

    # ── 7. Security ──────────────────────────────────────────────────────
    h1(document, "7. Security model")
    bullets(
        document,
        [
            "Tokens are verified on the server, always. The browser never decides who "
            "the player is.",
            "Sessions are opaque; the database stores only a SHA-256 digest, so a "
            "database leak does not leak live sessions.",
            "Passwords use Argon2id via PHP password_hash with per-password salting.",
            "Rate limiting: 10 requests per minute per IP on public auth endpoints, "
            "5 per minute on player connect; 429s use the standard error envelope.",
            "A strict Content-Security-Policy guards the app shell; no .env is "
            "committed and provider credentials never leave the backend.",
            "The MLBB ID is self-declared by design: the API returns mlbbIdVerified: "
            "false on every account payload so no client can mistake it for a fact.",
        ],
    )

    # ── 8. Quality ───────────────────────────────────────────────────────
    h1(document, "8. Testing and code quality")
    body(
        document,
        "57 PHPUnit tests, all passing, fully offline. Feature tests cover the whole "
        "auth lifecycle against faked verifiers; two dedicated suites exercise the "
        "real cryptographic path by signing tokens with a committed test RSA key and "
        "faking the key endpoints — covering bad signatures, wrong issuers and "
        "audiences, expiry, key rotation refetch, HS256 forgeries and upstream "
        "outages. The web side is checked by oxlint and a strict TypeScript build. "
        "Laravel Pint enforces code style.",
    )

    # ── 9. Q&A ───────────────────────────────────────────────────────────
    h1(document, "9. Prepared answers for technical questions")

    qa(
        document,
        "Why Laravel instead of FastAPI or Node?",
        "The first backend was Python FastAPI. We migrated to Laravel for the "
        "batteries-included layer we actually needed at this stage: migrations, "
        "validation form requests, middleware, rate limiting and a mature testing "
        "story, all in one framework, while preserving the exact same JSON contract "
        "so no client had to change. The migration proved the contract-first design: "
        "the React app did not change during the whole backend swap.",
    )
    qa(
        document,
        "Why React with Vite rather than Next.js?",
        "This is a client-rendered analytics dashboard behind an API — there is no "
        "SEO surface to render on the server. Vite gives sub-second cold builds, "
        "native ESM dev serving, and keeps the deployment story simple: a static "
        "bundle served by Laravel from one origin.",
    )
    qa(
        document,
        "How does ID-token verification work, and why not just decode the token?",
        "A JWT has three base64url parts. We decode the header to get the key id, "
        "fetch the provider's published public keys (Google JWKS or Firebase "
        "certificates), verify the RS256 signature with OpenSSL, then assert issuer, "
        "audience, expiry, issued-at and required claims. Decoding without verifying "
        "would let anyone forge an identity — the signature check against the "
        "provider's keys is the whole point of the design.",
    )
    qa(
        document,
        "Why store only a SHA-256 digest of the session token?",
        "The token is high-entropy, so a digest lookup is as fast as an index on the "
        "raw token, but a database leak reveals nothing usable: you cannot present a "
        "hash as a bearer token. It is the same reasoning as password hashing, "
        "applied to sessions.",
    )
    qa(
        document,
        "Why Argon2id?",
        "It is the PHP-recommended password algorithm: memory-hard, which makes "
        "GPU/ASIC cracking expensive, and it ships in PHP's password_hash with "
        "automatic salt handling. The code falls back to the platform default only "
        "if Argon2id is unavailable.",
    )
    qa(
        document,
        "Where does the tier data come from, and can it be wrong?",
        "From MLBBDex, which curates wiki-backed S+ to C tiers. It arrives through "
        "the same merge pipeline as every other field; if a hero has no tier we "
        "render an honest question-mark badge rather than guessing. Rankings numbers "
        "are Rone Arena observations over the chosen window.",
    )
    qa(
        document,
        "What happens when a provider is down?",
        "Three layers: the fast cache, then the durable database cache, then the "
        "live fetch. If the fetch fails the API answers 503 PROVIDER_UNAVAILABLE "
        "with a human-readable message, the UI shows an error state with a retry, "
        "and the failure is logged into provider_health. Outages degrade gracefully; "
        "they never fabricate data.",
    )
    qa(
        document,
        "Why are favourites stored client-side instead of in the database?",
        "The watchlist is personal preference, not shared state. Local storage keeps "
        "it instant, private and free of a write path, while the watchlist view still "
        "joins it with live rankings for tier, rank and movement. Moving it "
        "server-side later only requires an authenticated endpoint; the UI would not "
        "change.",
    )
    qa(
        document,
        "How does the comparison feature work?",
        "Each selected hero loads its detail and its 7-day trend through TanStack "
        "Query (cached, deduplicated). The page renders side-by-side cards with the "
        "best value highlighted, and merges the trend series date-by-date into one "
        "multi-line Recharts chart. The selection is encoded in the URL, so "
        "comparisons are shareable links.",
    )
    qa(
        document,
        "What does the service worker cache, and why not the API?",
        "Only the app shell: the HTML, hashed JS/CSS bundles, manifest and icons. "
        "Caching API responses would show stale rankings as if they were live — in "
        "an analytics product that is a lie. Offline the app shows its own error "
        "states instead.",
    )
    qa(
        document,
        "How does single-origin deployment avoid CORS?",
        "The built bundle is copied into Laravel's public directory, so the browser "
        "only ever talks to one origin. There are no cross-origin requests, so no "
        "CORS preflights and no origin allowlist to maintain.",
    )
    qa(
        document,
        "How would you scale this to production?",
        "Swap SQLite for Postgres (the migrations are portable; the schema has a "
        "Supabase bootstrap), serve PHP through FPM or Octane behind nginx, enable "
        "config and route caches, keep the rate limiters, and move the snapshot "
        "command onto the Laravel scheduler or a cron. The read path is already "
        "cache-first, so the providers are shielded from traffic.",
    )
    qa(
        document,
        "What was the hardest engineering problem here?",
        "Two stand out. Migrating FastAPI to Laravel without breaking a single "
        "client — solved by contract tests and keeping the envelope identical. And "
        "making token verification testable offline: the suite signs real RS256 "
        "tokens with a committed test key and fakes only the key endpoints, which "
        "caught a real environment-dependent bug in OpenSSL key construction that we "
        "fixed with a small DER encoder instead of relying on openssl_pkey_new.",
    )
    qa(
        document,
        "How do you keep the esports section honest?",
        "The standings provider publishes tables but not playoff match logs. Rather "
        "than inventing a bracket, the UI shows verified grand finals — each with "
        "champion, runner-up, series score, date and a link to its source — plus a "
        "verified-on date. The interface states this limitation explicitly.",
    )
    qa(
        document,
        "What would you build next?",
        "Server-side watchlist sync across devices, a CI pipeline running the 57 "
        "tests plus lint on every push, and completing the player-connect flow that "
        "links a player's own in-game statistics with their consent via a mailbox "
        "code.",
    )

    document.add_paragraph()
    closing = document.add_paragraph()
    closing_run = closing.add_run(
        "Prepared for the MLBB Tracker project — React + Vite client, Laravel API, "
        "Firebase accounts. All data flows are live; nothing is fabricated."
    )
    closing_run.font.color.rgb = MUTED

    OUT.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUT)
    print(f"OK: wrote {OUT}")


if __name__ == "__main__":
    build()
