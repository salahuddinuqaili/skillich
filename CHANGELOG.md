# Changelog

All notable rating changes and taxonomy updates are documented here.

## 0.2.0 — 2026-08 — Take your plan with you

The web app stopped being a browser and became a tool that gives you something
to keep.

### The plan
- **`skillich plan "<your job title>"`** — new command, and now the first one in
  `--help`. Type your title the way you'd say it out loud; get the invest /
  partner / delegate split, what "good" looks like at your next level, and a
  concrete way to prove you got there.
- **`--save plan.md`** writes the plan to a Markdown file you own.
- Each invest skill comes with a concrete way to prove you closed the gap, and
  the wording cycles so a leadership-heavy role doesn't print one sentence seven
  times.
- **`action_plan` MCP tool** — one call answers "what does AI mean for my job?"
  in Claude Desktop and Claude Code. Ambiguous titles return candidates to ask
  about instead of a confident guess.
- **`core/plan.py`** is the single source of truth for the action bands. The web
  app is generated with the same thresholds and copy inlined, so the three
  surfaces can't drift.

### Web app
- **Shareable URLs.** Every view has a real address (`#/plan/product/product_manager/senior`)
  and the browser Back button works. You can send someone your plan.
- **Download as Markdown, or print to PDF** — a dedicated print stylesheet drops
  the chrome and keeps the content.
- **Two steps, not three.** Type your role, and the plan appears with a level
  switcher on it — no wizard to walk back through.
- **Ranked search** with acronyms and aliases: `pm`, `sre`, `swe`, `sdr`, `ux`
  all land where you'd expect. Arrow keys and Enter work.
- **Career transitions** are precomputed and shown on your plan, with a
  side-by-side compare view and the exact skills you'd need to pick up.
- **Light and dark themes**, each with its own selected palette, following your
  system setting with a toggle that overrides it.
- **It paints immediately.** The headline and search box are static markup, so
  they render while the taxonomy is still downloading.
- **Accessibility**: real buttons, keyboard-reachable skill rows, ARIA combobox
  semantics, visible focus, skip link, reduced-motion support.
- **Resume where you left off** — your last plan is remembered locally. Nothing
  leaves your browser.
- Colour now follows the data-viz rules: status colour lives in a dot beside the
  label, never in the text, so nothing depends on hue alone.

### Fixed
- `skillich web` failed on a `pip install` — the `web` package was never
  included in the wheel.
- Multiple spaces in a search query ("product   manager") silently degraded an
  exact title match to a fuzzy one.
- Long share URLs were wrapped across lines in the terminal, breaking copy/paste.
- Career-transition similarity is memoised — precomputing all 88 roles went from
  minutes to ~4 seconds.

### Tests
- 265 Python tests (up from 173), plus 73 headless browser checks
  (`web/smoke.test.js`, jsdom) that drive the real generated page. Both run in CI.

---

## 2026-04 — Expansion & Refresh

### Taxonomy
- **17 functions** (+4: AI & Agents, Creative & Media, Research & Academia, Skilled Trades)
- **88 roles** (+20 new roles across new functions)
- **1,028 skills** (+213 new skills with per-skill AI impact ratings)
- All existing roles refreshed: `last_reviewed` updated to 2026-04
- Agentic AI items added to automating/augmenting lists across all functions
- Automation ratings adjusted upward by 0.05 for code generation, content creation, and data analysis skills

### Skills Guides
- **docs/skills.md** — Top 15 cross-functional skills for every AI user, with learning resources
- **docs/ai-skills.md** — Function-specific AI-optimised skill breakdowns with concrete workflows
- Both guides optimised for AI assistant consumption with structured metadata

### Assessment & Process
- **docs/assessment.md** — Self-assessment tool mapping 15 skills across 4 tiers to personalised recommendations
- **docs/review-process.md** — Quarterly review cadence with rating change protocol and confidence level framework

### Learning Resources
- **web/resources.json** expanded from 25 to 50+ keyword entries covering all 17 functions
- Learning resource links added to all 15 skills in skills.md

---

## 2025-09 — Initial Release

### Taxonomy
- **13 functions** covering Engineering, Product, Design, Data & Analytics, Marketing, Operations, Leadership, Finance, Legal, Sales, Customer Support, HR, Healthcare
- **68 roles** with full AI impact analysis
- **815 skills** with per-skill AI impact ratings (0.0-1.0)
- **~4,000 proficiency descriptions** from junior through principal
- All ratings set at `confidence: medium` (supported by published research and industry frameworks)

### Rating Methodology
- Ratings derived from: Anthropic Economic Index, GitHub Copilot Research, ILO 2024 automation studies, and role-specific industry sources
- Each role includes 2+ source citations
- All proficiency descriptions reviewed for minimum 120-character depth with observable behaviors

### Known Rating Gaps
- 82 skills rated exactly 0.5 (midpoint) — these reflect genuine uncertainty and will be prioritized for research-backed updates
- New function categories (Finance, Legal, Sales, Support, HR, Healthcare) are at `confidence: medium` pending practitioner validation
