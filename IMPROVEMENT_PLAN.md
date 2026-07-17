# skillich — Improvement Plan

> Created: 2026-07-17  
> Status: In progress  
> Method: Each phase is a separate PR against `main`. Tests must stay green. Ruff must stay clean.

---

## Phase 1 — Repo hygiene & MCP accuracy fix
**Branch:** `fix/repo-hygiene-mcp-accuracy`  
**Size:** ~30 min  
**Risk:** Zero — no logic changes

### Problems
1. `.claude/worktrees/` directories (two stale Claude Code worktrees) are not gitignored. They add 115+ files to `find` output, would be committed on `git add .`, and confuse contributors.
2. MCP server `instructions` string is hardcoded with stale numbers: "7 tech functions, 38 roles, 455 skills" — real counts are 17 functions, 88 roles, 1,028 skills. Every AI agent connecting via MCP gets wrong metadata about the tool it's using.
3. One unpushed local commit (`77a1d1f feat: add mcp config and architecture decisions`) — `main` is stale.

### Changes
- Add `.claude/worktrees/` to `.gitignore`
- Push the unpushed commit to `main` first
- In `mcp_server/server.py`: compute stats from live `_loader` at startup, build `instructions` dynamically
- Add a test: `test_mcp_server_instructions_reflects_live_taxonomy`

### Exit criteria
- `pytest -q` green
- `ruff check .` clean
- MCP server `instructions` reflects actual counts from the YAML files

---

## Phase 2 — CLI `--format` flag (scriptability)
**Branch:** `feat/cli-format-flag`  
**Size:** ~2h  
**Risk:** Low — additive only, defaults to current `rich` behaviour

### Problem
All `explore`, `analyze`, `assess`, `advise`, `path` CLI commands print rich terminal output (ANSI colors). Piping to another tool or script gives garbage. `SkillResult.to_dict()` already exists — it just isn't exposed.

### Changes
- Add `--format` / `-o` option to all commands: `rich` (default), `json`, `csv`
- `json` mode: print `json.dumps(result.data, indent=2)` to stdout, no color
- `csv` mode: use existing `cli/export.py` logic, print to stdout
- Update `cli/formatters.py` with a `format_output(result, fmt)` dispatcher
- Tests: parametrize each command with `--format json` and `--format csv`, assert parseable output and no ANSI codes

### Exit criteria
- `skillich explore --format json` prints valid JSON
- `skillich analyze --role backend --function engineering --format csv` prints valid CSV  
- All existing tests still pass

---

## Phase 3 — `skillich audit` staleness command
**Branch:** `feat/audit-command`  
**Size:** ~2h  
**Risk:** Low — new command, touches taxonomy loading only

### Problem
`RoleAIImpact.last_reviewed` field exists in the dataclass and YAML schema but is never surfaced. In a fast-moving AI landscape, a role last reviewed 12+ months ago can have significantly wrong automation ratings. No tooling exists to flag stale entries for maintainers or contributors.

### Changes
- New `skillich audit` CLI command with `--stale-after N` (days, default 180)
- Scans all roles, parses `last_reviewed` date, reports roles older than threshold
- Output includes: function, role, last_reviewed date, days since review, AI impact level, skill count
- `--format rich|json|csv` supported from day 1
- New `core/audit.py` module with `find_stale_roles(loader, days)` (pure, testable)
- Tests: mock taxonomy with known dates, assert correct stale/fresh classification

### Exit criteria
- `skillich audit --stale-after 180` lists all stale roles with dates
- `skillich audit --format json` outputs parseable JSON
- Unit tests for `find_stale_roles` covering: all fresh, all stale, missing date, mixed

---

## Phase 4 — Cross-function `compare_roles`
**Branch:** `feat/cross-function-compare`  
**Size:** ~1h  
**Risk:** Low — extends existing skill, backward compatible

### Problem
`AIImpactAnalyzerSkill.compare_roles` requires `function_id`, so you can only compare roles within one function. The most interesting comparison is cross-function (e.g., `marketing/content_writer` vs `engineering/backend`). `CareerAdvisorSkill.find_transitions` already does cross-function work — `compare_roles` should too.

### Changes
- In `ai_impact_analyzer.py`: make `function_id` optional in `compare_roles`
- If `function_id` omitted: compare across all functions (optionally limited by `limit`)
- Add `target_function_id` + `target_role_id` params for two-role direct comparison mode
- Update MCP server tool docstring
- Tests: cross-function comparison, two-role direct compare, existing single-function still works

### Exit criteria
- `skillich analyze --action compare_roles` (no function) returns top N roles by impact across all functions
- Direct two-role compare: `--source engineering/backend --target marketing/content_writer`
- All existing `compare_roles` tests still pass

---

## Phase 5 — Ollama career-summary skill
**Branch:** `feat/ollama-career-summary`  
**Size:** ~3h  
**Risk:** Medium — requires Ollama running; skill must degrade gracefully without it

### Problem
`skills/local/local_llm.py` exists as a stub (generic text summarizer). Given the Ollama stack already running locally (qwen2.5-coder:14b, gemma4:e4b), there's a more valuable skill: **personalized career summary** — take a role's taxonomy data and generate a human-readable "what this means for your career" paragraph using the local model. This aligns with the per-x governance (career data stays local).

### Changes
- New `skills/taxonomy_skills/career_narrator.py`: `CareerNarratorSkill`
  - `action='role_summary'`: given function+role, load taxonomy data, build a structured prompt, call Ollama `/api/chat` (streaming=False), return narrative paragraph
  - `action='skill_advice'`: given a skill name + user's current level, generate concrete next-step advice
  - Graceful degradation: if Ollama unreachable, return `SkillStatus.PARTIAL` with raw taxonomy data + error message (never hard-fail)
- `OLLAMA_ENDPOINT` env var (default `http://localhost:11434`), `OLLAMA_MODEL` env var (default `qwen2.5-coder:14b`)
- Register in CLI (`skillich narrate`) and MCP server
- Tests: mock `requests.post`, assert prompt shape, assert graceful degradation path

### Exit criteria
- `skillich narrate --function engineering --role backend` calls Ollama and prints a narrative
- Without Ollama running: returns partial result with raw data, exit 0
- Tests pass without Ollama (mocked)

---

## Phase 6 — PyPI publish workflow
**Branch:** `feat/pypi-publish`  
**Size:** ~1h  
**Risk:** Low on code; one-time PyPI token setup needed

### Problem
README says "install from source." `pyproject.toml` is fully configured but no publish pipeline exists. `pip install skillich` is blocked.

### Changes
- `.github/workflows/publish.yml`: trigger on `v*` tag push
  - Build: `python -m build`
  - Publish to PyPI via `pypa/gh-action-pypi-publish`
  - Uses `PYPI_API_TOKEN` GitHub secret (you set this once)
- Bump `pyproject.toml` description to reflect current counts (88 roles, 1,028 skills)
- Add `python -m build` step to existing `ci.yml` to catch packaging errors on every PR
- Update README install instructions: `pip install skillich` (primary), "from source" (secondary)

### Exit criteria
- `python -m build` produces a valid wheel + sdist
- CI includes the build step
- On `git tag v0.2.0 && git push --tags`, publish workflow triggers
- `pip install skillich` works after first publish (manual verification after merge)

---

## Summary table

| Phase | Branch | What | Risk | PR |
|-------|--------|------|------|-----|
| 1 | `fix/repo-hygiene-mcp-accuracy` | gitignore + dynamic MCP instructions | None | #1 |
| 2 | `feat/cli-format-flag` | `--format json/csv` on all commands | Low | #2 |
| 3 | `feat/audit-command` | `skillich audit --stale-after N` | Low | #3 |
| 4 | `feat/cross-function-compare` | cross-function `compare_roles` | Low | #4 |
| 5 | `feat/ollama-career-summary` | Ollama-backed career narrator skill | Medium | #5 |
| 6 | `feat/pypi-publish` | PyPI publish workflow | Low | #6 |
