"""Update docs/PROJECT_EXPLANATION_SCRIPT.docx for the v0.12.0 shipping state.

Adds the deployment-and-distribution story (Windows release, Render + GitHub
Pages, Docker, AI-generated icon), refreshes affected Q&A answers, and
renumbers the later sections.
"""

import copy

import docx
from docx.text.paragraph import Paragraph

DOC = "docs\\PROJECT_EXPLANATION_SCRIPT.docx"
EMDASH = "\u2014"


def set_text(paragraph, text: str) -> None:
    """Replace a paragraph's text, keeping its style and first-run formatting."""
    paragraph.runs[0].text = text
    for run in paragraph.runs[1:]:
        run._element.getparent().remove(run._element)


def insert_after(anchor, text: str, style: str):
    """Insert a new paragraph after `anchor` and return it (styles preserved)."""
    new = doc.add_paragraph(text, style=style)
    anchor._p.addnext(new._p)
    return new


def insert_before(anchor, text: str, style: str):
    """Insert a new paragraph before `anchor` and return it (styles preserved)."""
    new = doc.add_paragraph(text, style=style)
    anchor._p.addprevious(new._p)
    return new


def clone_before(anchor, source_paragraph):
    """Insert a copy of `source_paragraph` before `anchor` (keeps its style),
    then return the copy so its text can be set."""
    new_el = copy.deepcopy(source_paragraph._p)
    anchor._p.addprevious(new_el)
    return Paragraph(new_el, anchor._parent)


doc = docx.Document(DOC)
paras = doc.paragraphs

# ---------------------------------------------------------------- subtitle --
sub = paras[1]
set_text(
    sub,
    "Project Explanation & Defense Script "
    + EMDASH
    + " React + Vite web app, Laravel API, Firebase accounts, MLBB-inspired "
    "design. Shipped as release v0.12.0: packaged Windows download plus "
    "Render and GitHub Pages deployment configs. Prepared November 2026.",
)

# ------------------------------------------------- 6.5 PWA + download page --
pwa = paras[39]
set_text(
    pwa,
    "Install the app from the address bar or /download. A service worker "
    "caches the shell only " + EMDASH + " API responses are never cached, so "
    "offline you get honest error states, not stale numbers pretending to be "
    "live. /download serves the Android APK with version, size and SHA-256. "
    "Windows users get the full app as a self-contained zip from the GitHub "
    "Releases page (section 7).",
)

# ------------------------------- new section 7 after the 6.5 body paragraph --
heading7 = insert_after(
    pwa, "7. Deployment and distribution", style="Heading 1"
)
intro = insert_after(
    heading7,
    "Same codebase, three shipping channels. The primary deployment stays "
    "single-origin: the built React bundle is copied into Laravel's "
    "public/app directory, so one server serves both the app and the API.",
    style="Normal",
)
bullets = [
    "Windows package (shipped): GitHub Release v0.12.0 carries a 50 MB zip "
    "with a slimmed PHP 8.4.28 runtime, the Laravel API with its vendor "
    "tree, the built React SPA and an empty SQLite database. "
    "START-MLBB-TRACKER.bat runs migrations on first boot, starts the "
    "server and opens http://127.0.0.1:8000 " + EMDASH + " no PHP, Composer "
    "or Node install required on the target machine. The package is "
    "smoke-tested end to end (fresh extract, migrate, serve, health check) "
    "and ships an empty database so no developer data leaks.",
    "Public URL (configured): a multi-stage Dockerfile builds the SPA in a "
    "Node stage and runs it on PHP 8.4 with pdo_sqlite/pgsql; render.yaml "
    "is a Render Blueprint that deploys the container on the free tier with "
    "a health check on /api/v1/health and auto-deploy on every push to "
    "main. The full walkthrough lives in docs/DEPLOY_RENDER.md.",
    "Split-origin option (configured): scripts/deploy_pages.ps1 builds the "
    "React app for GitHub Pages with VITE_API_BASE pointed at the Render "
    "API, fixes absolute paths for the /mlbbtracker/ sub-path, adds a "
    "404.html SPA fallback and force-pushes the gh-pages branch. The API "
    "allowlists the Pages origin through MLBB_CORS_ALLOWED_ORIGINS in "
    "server/config/cors.php.",
    "App icon: AI-generated " + EMDASH + " a navy shield with a glowing "
    "electric-blue analytics line " + EMDASH + " and processed by "
    "scripts/process_ai_icon.py into the full PWA set: 192 and 512 px any "
    "and maskable icons, the apple-touch icon and the favicon. The pipeline "
    "is repeatable: regenerate the source image, rerun the script, and "
    "every icon updates.",
]
anchor = intro
for bullet in bullets:
    anchor = insert_after(anchor, bullet, style="List Bullet")

# ------------------------------------------------------- renumber headings --
for p in doc.paragraphs:
    if p.style.name == "Heading 1":
        if p.text.startswith("7. Security model"):
            set_text(p, "8. Security model")
        elif p.text.startswith("8. Testing and code quality"):
            set_text(p, "9. Testing and code quality")
        elif p.text.startswith("9. Prepared answers"):
            set_text(p, "10. Prepared answers for technical questions")

# ------------------------------------------------- refresh two Q&A answers --
for p in doc.paragraphs:
    if p.text.startswith("A: The built bundle is copied into Laravel"):
        set_text(
            p,
            "A: The built bundle is copied into Laravel's public directory, "
            "so the browser only ever talks to one origin. There are no "
            "cross-origin requests, so no CORS preflights and no origin "
            "allowlist to maintain. For split deployments " + EMDASH + " a "
            "GitHub Pages frontend calling a Render-hosted API " + EMDASH
            + " the frontend reads VITE_API_BASE and the API allowlists "
            "exact origins through MLBB_CORS_ALLOWED_ORIGINS.",
        )
        break

for p in doc.paragraphs:
    if p.text.startswith("A: Swap SQLite for Postgres"):
        set_text(
            p,
            "A: Swap SQLite for Postgres (the migrations are portable; the "
            "schema has a Supabase bootstrap), serve PHP through FPM or "
            "Octane behind nginx, enable config and route caches, keep the "
            "rate limiters, and move the snapshot command onto the Laravel "
            "scheduler or a cron. The read path is already cache-first, so "
            "the providers are shielded from traffic. The container story "
            "already ships: a multi-stage Dockerfile and a render.yaml "
            "Blueprint put the API on Render with a health check and "
            "auto-deploy on push.",
        )
        break

# ------------------------------------------------------ three new Q&As ------
footer = next(
    p for p in doc.paragraphs if p.text.startswith("Prepared for the MLBB Tracker project")
)
qa_template = next(
    p for p in doc.paragraphs if p.text.startswith("Q: How does single-origin deployment")
)

new_qas = [
    (
        "Q: How is the app distributed?",
        "A: Three ways from one codebase. The single-origin app serves the "
        "React bundle straight from Laravel; GitHub Release v0.12.0 carries "
        "the packaged Windows zip; and the Render plus GitHub Pages configs "
        "publish a public URL. Every channel serves the same API contract "
        "and the same verified data.",
    ),
    (
        "Q: What is inside the Windows download, and why bundle PHP?",
        "A: A self-contained zip: a slimmed PHP 8.4.28 runtime, the Laravel "
        "API with its vendor tree, the built React SPA and an empty SQLite "
        "database. One double-click runs migrations and serves the app at "
        "http://127.0.0.1:8000. Bundling PHP means zero prerequisites " + EMDASH
        + " no PHP, Composer or Node install on the target machine " + EMDASH
        + " and the package was verified end to end before publishing.",
    ),
    (
        "Q: Where does the app icon come from?",
        "A: It is an AI-generated image of a navy shield with a glowing "
        "analytics line, run through scripts/process_ai_icon.py to produce "
        "the whole PWA icon set " + EMDASH + " rounded any icons, full-bleed "
        "maskable icons, the apple-touch icon and the favicon. Regenerating "
        "the source and rerunning the script refreshes every icon at once.",
    ),
]
for question, answer in new_qas:
    question_paragraph = clone_before(footer, qa_template)
    set_text(question_paragraph, question)
    answer_paragraph = clone_before(footer, qa_template)
    set_text(answer_paragraph, answer)

# ------------------------------------------------------------------ footer --
set_text(
    footer,
    "Prepared for the MLBB Tracker project " + EMDASH + " React + Vite "
    "client, Laravel API, Firebase accounts. Shipped as release v0.12.0: "
    "single-origin web app, packaged Windows download, Render and GitHub "
    "Pages deployment configs. All data flows are live; nothing is "
    "fabricated.",
)

doc.save(DOC)
print("saved", DOC)
