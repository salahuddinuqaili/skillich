# skillich — Handoff Notes
> Updated: 2026-08-22

---

## State: v0.2.0 ready to ship

Branch `feat/plan-v2`. 268 Python tests + 75 headless browser checks passing, ruff clean.

**What shipped in this release:** see [CHANGELOG.md](CHANGELOG.md#020--2026-08--take-your-plan-with-you).
Short version — the plan is now a thing you can keep: shareable URL, Markdown download,
print-to-PDF, `skillich plan` in the terminal, and an `action_plan` MCP tool.

---

## ONE ACTION NEEDED FROM YOU — PyPI publish

The publish workflow is ready but needs a one-time PyPI setup:

1. Go to https://pypi.org → Your account → Publishing → **Add trusted publisher**
   - Owner: `salahuddinuqaili`
   - Repo: `skillich`
   - Workflow: `publish.yml`
   - Environment: `pypi`
2. Then run:
   ```bash
   cd C:\Users\mulli\projects\skillich
   git tag v0.2.0 && git push --tags
   ```
3. GitHub Actions fires automatically — no API token or secrets needed (OIDC).

After that, `pip install "skillich[cli]"` works for everyone.

GitHub Pages deploys on merge to `main` — no action needed there.

---

## How to work on this

```bash
# Python
pytest -q                        # 268 tests
ruff check .

# Web app — regenerate, then drive the real page in jsdom
python web/generate.py           # writes web/index.html (gitignored, ~4s)
npm --prefix web ci              # once
node web/smoke.test.js           # 75 checks

# Look at it
python -m http.server 8899 --directory web
```

Markup lives in `web/template.html`, not inside `generate.py`. The action-band
thresholds live in `core/plan.py` and are inlined into the page at build time —
change them there and the CLI, MCP server and web app all follow
(see ADR-9 in ARCHITECTURE_DECISIONS.md).

---

## What to do next

### Option A — Distribution (highest value now that the plan is shareable)
The plan URL is the shareable unit. Every post should link to a *specific* plan,
not the homepage:
- `.../#/plan/marketing/content_strategist/mid` — the most exposed function
- `.../#/plan/trades/electrician/journeyman` — the most resilient
- Show HN / Product Hunt / LinkedIn, led by one finding: trades 21% vs marketing 54%

### Option B — Taxonomy freshness
`skillich audit --stale-after 180`. Ratings decay; the 2026 landscape has moved
since some were written. Refreshing 5–10 roles and bumping `last_reviewed` is
high-trust, low-effort work.

### Option C — Earn the "high" confidence level
Every role is `medium` confidence today. The path to `high` is practitioner
validation. The plan page already ends with a prefilled feedback link; the next
step is making it specific enough to answer in one click — e.g. thumbs up/down
per skill rating rather than a free-text issue.

### Option E — Modernise typing, deliberately
Ruff's rule set is pinned to `E4, E7, E9, F` in pyproject because newer ruff
releases enable `UP` by default and flag 128 `typing.Dict`/`List` uses across
files nobody touched. Migrating to builtin generics (`dict[str, Any]`) and then
widening `select` is worthwhile — as its own PR, not folded into a feature.

### Option D — Roles people ask for that don't exist
Search returns nothing for `nurse`, `teacher` or `doctor` — healthcare covers
informatics and coding roles, not clinical ones, and education isn't covered at
all. The empty state already invites a role request; watch what gets asked for.

---

*Resume by reading this file, then `git log --oneline -10`.*
