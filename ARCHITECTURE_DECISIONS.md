# Architecture Decision Records

This document captures the significant architectural decisions made in skillich — an open-source career taxonomy covering 88 roles, 1,028 skills, and 17 functions, each rated for AI impact.

---

## ADR-1: YAML files as the single source of truth, not a database

**Context:**
The taxonomy needs to be editable by practitioners (accountants, engineers, electricians) who validate AI impact ratings from their experience. It also needs to be auditable — when a rating changes from 0.45 to 0.50, reviewers should see exactly what changed, when, and why. Traditional databases make both of these workflows difficult.

**Decision:**
Store all taxonomy data as YAML files in version control, organised by function directory. Each role is a single `.yaml` file containing its full definition: description, AI impact analysis, proficiency levels, and skills with ratings. No database, no ORM, no migrations.

**Trade-offs:**
- *Given up:* Query performance at scale. Searching 1,028 skills requires loading all files into memory. Full-text search across proficiency descriptions is O(n).
- *Given up:* Concurrent write access. Two contributors editing the same role file will create a merge conflict.
- *Accepted risk:* The taxonomy is small enough (~105 files, ~12K lines of YAML) that in-memory loading is instant. Git handles merge conflicts well for structured text. If the taxonomy grows to 10,000+ roles, this decision would need revisiting.
- *Gained:* Every rating change is a git diff. Practitioners edit YAML directly without learning a CMS. The entire taxonomy can be forked, customised, and re-hosted with zero infrastructure.

**Status:** Accepted

---

## ADR-2: Plugin skill architecture with registry pattern and multi-provider export

**Context:**
The taxonomy data needs to be accessible through multiple AI platforms (Claude via MCP, ChatGPT via function calling, direct API via Anthropic tool_use) as well as traditional interfaces (CLI, web, Python SDK). Each platform has its own tool definition format, but the underlying skill logic is identical.

**Decision:**
Define an abstract `Skill` base class with a standardised interface (`name`, `description`, `parameters` as JSON Schema, `execute(**kwargs) -> SkillResult`). Implement a `SkillRegistry` that discovers, validates, and exposes skills. Each skill can export itself to OpenAI, Anthropic, and MCP formats via `to_openai_tool()`, `to_anthropic_tool()`, and `to_mcp_tool()` methods on the registry.

**Trade-offs:**
- *Given up:* Simplicity. A single-purpose CLI would be 200 lines of code. The registry pattern adds ~400 lines of abstraction.
- *Given up:* Platform-specific optimisation. The lowest-common-denominator parameter schema means no platform gets to use its unique features (e.g., Anthropic's cache_control on tool definitions).
- *Accepted risk:* The abstraction is only justified if multiple interfaces are actually used. Currently, MCP and CLI are active; the OpenAI and Anthropic adapters are lightly used.
- *Gained:* Adding a new skill requires implementing one class. It immediately works across all interfaces. Adding a new platform requires one export method, not touching every skill.

**Status:** Accepted

---

## ADR-3: Static single-page app over server-rendered web application

**Context:**
The web interface needs to let anyone browse 88 roles and 1,028 skills, search by name, and get a personalised action plan — without requiring signup, a backend, or hosting costs. The target audience includes non-technical users who should be able to access the tool in 60 seconds.

**Decision:**
Generate a single HTML file (`web/index.html`) with the entire taxonomy embedded as JSON. The build script (`web/generate.py`) reads all YAML files, converts them to a JSON blob, and injects it into an HTML template with vanilla JavaScript for search, filtering, and the assessment wizard. Deploy via GitHub Pages on every push to main.

**Trade-offs:**
- *Given up:* Dynamic features. No user accounts, no saved assessments, no server-side analytics. The assessment state lives only in the browser session.
- *Given up:* Page size efficiency. The generated HTML is ~2MB with the full taxonomy embedded. This is large for a web page but loads in under 2 seconds on modern connections.
- *Accepted risk:* If the taxonomy grows 10x, the embedded JSON approach won't scale. At that point, a lightweight API or static JSON fetch would be needed.
- *Gained:* Zero hosting costs (GitHub Pages). Zero operational burden (no server to monitor). Works offline once loaded. No CORS, auth, or API rate limiting to worry about.

**Status:** Accepted

---

## ADR-4: Only pyyaml as a required dependency

**Context:**
The project serves multiple audiences — practitioners who just want to browse YAML files, developers who want the Python SDK, and power users who want CLI/MCP integration. Forcing everyone to install MCP libraries, Typer, or jsonschema to use the core taxonomy loader would create unnecessary friction.

**Decision:**
Make `pyyaml` the only required dependency. Everything else is optional, installed via extras: `skillich[cli]` for Typer, `skillich[mcp]` for Model Context Protocol, `skillich[dev]` for testing and schema validation, `skillich[openai]` and `skillich[anthropic]` for platform adapters. Runtime parameter validation uses stdlib-only type checking (`core/validation.py`), with `jsonschema` available as an optional upgrade.

**Trade-offs:**
- *Given up:* Guaranteed validation depth. Without `jsonschema`, invalid YAML structures are only caught at field-access time, not at load time. CI catches these, but local development might not.
- *Given up:* Simplified install instructions. Users need to know which extras they want (`pip install skillich[cli,mcp]` vs. `pip install skillich`).
- *Gained:* The core library (`from core.taxonomy import TaxonomyLoader`) works with just `pip install pyyaml`. No compiled dependencies, no platform-specific wheels, no version conflicts.

**Status:** Accepted

---

## ADR-5: Quantified AI impact scores (0.0-1.0) with structured automating/augmenting/preserving lists

**Context:**
Career advice about AI typically falls into two failure modes: vague reassurance ("AI won't replace you") or vague alarm ("AI is coming for your job"). Neither is actionable. Practitioners need to know *which specific skills* in their role are being automated, which are being augmented, and which remain fully human.

**Decision:**
Rate every skill on a 0.0 (fully human) to 1.0 (fully automated) scale, with a free-text `detail` field explaining the rating. At the role level, provide three structured lists: `automating` (tasks AI is absorbing), `augmenting` (tasks where AI amplifies humans), and `preserving` (tasks that remain fully human). Include `confidence` levels (low/medium/high) and `last_reviewed` dates to signal data freshness.

**Trade-offs:**
- *Given up:* Precision. A single number can't capture the nuance of "0.5 at a legacy enterprise vs. 0.7 at an AI-native startup." The `detail` field compensates, but the number is what gets sorted and compared.
- *Given up:* Stability. Ratings decay as AI capabilities improve. A quarterly review cadence is documented, but ratings will always lag reality by weeks to months.
- *Accepted risk:* Unvalidated ratings could mislead career decisions. The `confidence: medium` flag and practitioner feedback mechanisms mitigate this, but most ratings are still expert estimates, not empirical measurements.
- *Gained:* Actionable, comparable, sortable data. "Electrical Installation is 0.05, CRM Data Entry is 0.90" is immediately useful. The automating/augmenting/preserving framework gives users a concrete mental model for their role.

**Status:** Accepted

---

## ADR-6: Observable proficiency descriptions, not knowledge claims

**Context:**
Career frameworks often describe levels in terms of knowledge ("understands distributed systems") rather than observable behaviors ("designs systems that handle distributed coordination challenges including leader election and distributed locking"). Knowledge claims are hard to assess and easy to inflate. The taxonomy needs proficiency descriptions that a manager, a self-assessor, or an AI assistant can actually evaluate against.

**Decision:**
Require every proficiency description to use observable language — what someone *does* at each level, not what they *know*. Content validation (`core/content_validator.py`) flags descriptions below a minimum word count and checks for weak verbs like "understands" or "is familiar with." Each skill has descriptions for 4-5 levels, creating ~4,000+ proficiency descriptions that serve as a career ladder.

**Trade-offs:**
- *Given up:* Brevity. Observable descriptions are longer than knowledge claims ("Designs authorization architectures supporting RBAC and ABAC models across multiple services" vs. "Knows auth patterns"). This makes YAML files verbose (~500 lines per role).
- *Given up:* Easy contribution. Writing observable proficiency descriptions requires domain expertise. A practitioner can validate a rating in 2 minutes, but writing a new role from scratch takes significant effort.
- *Gained:* The proficiency descriptions are useful beyond the taxonomy — as interview rubrics, performance review frameworks, and career ladder definitions. They're the foundation for the skill assessor and learning path skills.

**Status:** Accepted

---

## ADR-7: Dual-layer validation — structural schema plus content quality

**Context:**
YAML is flexible enough to accept almost any structure. A file could pass YAML parsing but contain a skill with no description, a rating of 2.5 (outside the 0.0-1.0 range), or proficiency descriptions that are one word long. Schema validation catches structural issues but not quality issues.

**Decision:**
Implement three validation layers:
1. **JSON Schema** (`core/schema_validator.py`) — validates structure: required fields, type correctness, enum values, array lengths (5-20 skills per role). Uses `jsonschema` library, runs in CI.
2. **Content quality** (`core/content_validator.py`) — validates substance: minimum description length, rating clustering (flags too many skills at exactly 0.5), source coverage, proficiency depth. Runs in CI as warnings.
3. **Parameter validation** (`core/validation.py`) — validates runtime inputs to skills: required parameters, type checking, enum constraints. Uses stdlib only, runs at every skill invocation.

**Trade-offs:**
- *Given up:* Speed. Three validation passes add complexity and CI time. For 105 files, this is negligible (~2 seconds), but it's more code to maintain.
- *Accepted risk:* Content quality checks are informational, not blocking. A role with thin descriptions can still merge if the reviewer approves it. This is intentional — it's better to have a contributed role with thin descriptions than no role at all.
- *Gained:* Confidence that the taxonomy is both structurally valid and substantively useful. Schema validation catches bugs; content validation catches laziness.

**Status:** Accepted

---

## ADR-8: Skills guides optimised for AI assistant consumption

**Context:**
The taxonomy data is in YAML — great for machines, but not directly useful when a user pastes it into an AI conversation and asks "what should I learn?" The skills guides (`docs/skills.md`, `docs/ai-skills.md`, `docs/assessment.md`) need to work both as human-readable documents AND as effective context for AI assistants giving career advice.

**Decision:**
Structure the markdown guides with explicit AI assistant instructions (blockquote at top), structured tables with consistent column formats, role-to-skill mappings for personalisation, concrete AI workflow examples per skill, and self-assessment rubrics with scoring logic. Include cross-references to the YAML taxonomy for deeper data. Design the files so that an AI reading them can immediately walk a user through assessment, identify gaps, recommend specific skills, and suggest learning resources — without needing to parse YAML.

**Trade-offs:**
- *Given up:* Conciseness. The AI-optimised format is more verbose than a simple skill list. `skills.md` is 200 lines where a plain list would be 30.
- *Given up:* Single-audience optimisation. The files serve both humans browsing GitHub and AI assistants processing context. This means some content (like the blockquote instructions) looks odd to human readers.
- *Accepted risk:* AI assistant behavior is non-deterministic. The guides structure recommendations, but different AI models will interpret and apply them differently.
- *Gained:* The guides are immediately useful as RAG context, system prompt material, or MCP-served resources. A user can paste `skills.md` into any AI chat and get personalised career advice grounded in the taxonomy data.

**Status:** Accepted

---

## ADR-9: One plan engine in Python, its rules inlined into the web app

**Context:**
The action plan (invest / partner / delegate, the level gap, the exposure band) has to exist in three places: the CLI, the MCP server, and a static web page that cannot run Python. Writing the rules twice guarantees the browser and the terminal eventually disagree about where the 30% line sits.

**Decision:**
`core/plan.py` owns the thresholds, the band copy, the proof points, the query synonyms and the confidence rule. `plan_constants()` serialises them to JSON and `web/generate.py` inlines that into the page at build time; the page's JavaScript reads the constants rather than hard-coding them. `tests/test_web_generate.py` asserts the shipped constants equal the Python ones, so a change in one place fails the build if it doesn't reach the other.

**Trade-offs:**
- *Given up:* Runtime independence of the web page from the Python codebase — the page must be regenerated when the rules change. CI does this on every push.
- *Given up:* The plan *algorithm* is still written twice (Python `build_plan`, JS `buildPlan`). Only the constants are shared. A behavioural divergence in the traversal is possible; the jsdom suite checks band partitioning across all 88 roles to catch it.
- *Accepted risk:* The JSON blob grows with the copy. It is a few kilobytes against a multi-megabyte page.
- *Gained:* One place to argue about where "invest" ends. Adding a fourth surface costs nothing new.

**Status:** Accepted

---

## ADR-10: Markup in a template file, and a static hero above the payload

**Context:**
The generated page is ~2.6 MB, because the entire taxonomy including five proficiency descriptions per skill is inlined. Every view was rendered by JavaScript, so nothing appeared on screen until the whole file had downloaded — the worst possible first impression for a tool whose promise is "60 seconds". The markup also lived as a 400-line string literal inside `generate.py`, where it was unreviewable.

**Decision:**
Move the markup to `web/template.html`, a real HTML file with `__PLACEHOLDER__` tokens that `generate.py` fills. Put the headline, the search input and the value proposition in the template as static markup, and stream the taxonomy in a `<script type="application/json">` block at the foot of the document. The router renders into a `#view` element below the static hero. Splitting data out also lets `_script_safe()` escape `<` so taxonomy prose can never close its own script tag.

**Trade-offs:**
- *Given up:* The single-file source. Markup and generator are now two files that must agree on the placeholder names; `render()` raises if any placeholder is missing rather than silently shipping a broken page.
- *Given up:* Some duplication — the static hero's markup is not generated from the same code path as the rest of the home view.
- *Rejected:* Fetching the taxonomy as a separate JSON request. It would cut first paint further but breaks the "one file you can email or open offline" property, which `skillich web` depends on.
- *Gained:* First paint no longer waits on 2.6 MB. The template is diffable and reviewable, which is what made the accessibility and theming work tractable at all.

**Status:** Accepted

---

## TPM Narrative

skillich is built around one core insight: career advice about AI is only useful if it's specific enough to act on. Telling someone "AI will change your job" is obvious. Telling them "your CRM Data Entry skill is 90% automatable, but your Conflict Resolution skill is 5% automatable — here's where to invest" is actionable. The architecture reflects this: a YAML taxonomy of 1,028 skills across 88 roles, each with a quantified AI impact rating, observable proficiency descriptions at 4-5 career levels, and structured lists of what's being automated, augmented, and preserved. Every design choice optimises for two things: practitioner trust (ratings are auditable, versioned, and open to correction) and multi-interface access (the same data serves a web app, CLI, MCP server for Claude, and function calling for ChatGPT).

The system deliberately avoids a database, a backend server, and user accounts. The taxonomy is YAML files in git — practitioners review ratings through pull requests, not admin panels. The web app is a single generated HTML file deployed to GitHub Pages with zero operational cost. The plugin architecture means adding a new skill (like a career transition analyzer) requires one Python class that immediately works across every interface. This isn't engineering minimalism for its own sake — it's a bet that the taxonomy's value comes from data quality and coverage, not from infrastructure complexity. The quarterly review cadence, confidence levels, and practitioner validation pipeline exist because a stale or unvalidated rating is worse than no rating at all.

What makes this interesting from a product perspective is the dual-audience design. The skills guides aren't just documentation — they're structured so that an AI assistant reading them can immediately personalise career recommendations. The self-assessment maps 15 skills across 4 tiers to concrete next steps. The YAML taxonomy feeds Claude via MCP and ChatGPT via function calling. This means skillich works both as a static reference that humans browse and as live context that AI tools consume — which is exactly the kind of human-AI collaboration the taxonomy itself is trying to help people navigate.
