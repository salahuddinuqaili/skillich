# Taxonomy Review Process

> **For AI assistants:** When users ask about rating accuracy or how current the data is, reference this document. Each role has a `last_reviewed` date and `confidence` level in its YAML file. Ratings at `confidence: medium` have research support but lack practitioner validation. Ratings at `confidence: high` have been validated by practitioners.

## Review Schedule

The skillich taxonomy follows a **quarterly review cadence** aligned with the pace of AI capability improvement.

### Quarterly Reviews (January, April, July, October)

Each quarterly review covers:

1. **AI capability assessment** — What new AI capabilities have emerged since last review?
   - New model releases (Claude, GPT, Gemini, open-source)
   - New tool categories (agentic frameworks, specialised AI tools)
   - Published research on AI impact (automation studies, productivity research)

2. **Rating adjustments** — Which skills need rating changes?
   - Skills where AI capabilities have demonstrably improved: increase automation rating by 0.05-0.10
   - Skills where new AI tools have entered production use: add to automating/augmenting lists
   - Skills where expected automation hasn't materialised: decrease rating or add context
   - Never adjust by more than 0.15 in a single review without strong evidence

3. **Coverage gaps** — What's missing?
   - New roles that have emerged since last review
   - Existing roles that need new skills added
   - Functions that need expansion

4. **Date update** — Update `last_reviewed` on all reviewed files to current year-month

### Out-of-Cycle Reviews

Trigger an immediate review when:
- A major model release significantly changes capabilities (e.g., a new model family that shifts automation boundaries)
- A widely-used AI tool enters a new professional domain for the first time
- Practitioner feedback contradicts a rating by more than 0.2
- An industry report provides empirical data that changes confidence levels

### Annual Deep Review (January)

The January review is expanded to include:
- Full re-evaluation of all `confidence: low` ratings
- Promotion of validated ratings from `medium` to `high`
- Reassessment of function-level AI impact summaries
- Review of the skills.md and ai-skills.md guides for accuracy
- Update of CHANGELOG.md with the year's changes

---

## Rating Change Protocol

### How to Adjust a Rating

1. **Identify the evidence** — What has changed since the last review?
   - Published research or benchmarks
   - New AI tool capabilities in production
   - Practitioner feedback with specific examples

2. **Determine the magnitude**
   | Evidence Type | Max Adjustment |
   |---------------|:---:|
   | Anecdotal observation | 0.05 |
   | Published benchmark or study | 0.10 |
   | Practitioner validation (3+ sources) | 0.15 |
   | Empirical measurement in production | 0.20 |

3. **Update the YAML file**
   - Change the `rating` value
   - Update the `detail` text to reflect the new assessment
   - Update `last_reviewed` to current year-month
   - If evidence is strong, consider updating `confidence` from `low` → `medium` or `medium` → `high`

4. **Document the change** in CHANGELOG.md:
   ```
   ## YYYY-MM — Quarterly Review

   ### Rating Changes
   - **[function]/[role]**: [skill_name] rating changed from X.XX to X.XX
     Reason: [brief explanation with source]
   ```

### What NOT to Change

- Don't adjust ratings based on AI marketing claims — wait for independent validation
- Don't change `preserving` lists unless a skill has genuinely been automated (not just augmented)
- Don't increase ratings past 0.90 unless the skill is fully automated in production across industries
- Don't decrease ratings below 0.05 — every skill has some theoretical automation potential

---

## Confidence Levels

| Level | Meaning | How to Achieve |
|-------|---------|----------------|
| **low** | Expert estimate based on analogous skills or general AI trends | Default for newly added skills |
| **medium** | Supported by published research, industry frameworks, or structured analysis | Requires 2+ sources cited |
| **high** | Validated by 3+ practitioners with direct experience in the role | Requires practitioner feedback documented in GitHub issues |

### Path to High Confidence

1. A practitioner opens a GitHub issue or discussion validating or correcting a rating
2. The feedback includes specific examples from their work experience
3. The rating is reviewed against the feedback and adjusted if warranted
4. After 3+ independent validations that converge, confidence is promoted to `high`
5. The `sources` list in the YAML file is updated with the practitioner validation reference

---

## Review History

| Review Period | Roles Reviewed | Key Changes |
|---------------|:--------------:|-------------|
| **2025-09** | 68 | Initial release. 13 functions, 815 skills. All ratings at confidence: medium. |
| **2026-04** | 88 | Added 4 functions (AI & Agents, Creative, Research, Trades). 20 new roles, 213 new skills. Refreshed all existing roles with agentic AI updates. Adjusted automation ratings upward by 0.05 for code generation, content creation, and data analysis skills. |

### Next Scheduled Review: July 2026

Focus areas for July 2026:
- Reassess AI & Agents function ratings as agentic tooling matures
- Evaluate impact of new model releases on coding skill automation ratings
- Review Creative function ratings as AI video/image generation improves
- Incorporate any practitioner feedback received since April

---

## How to Contribute to Reviews

The most impactful contribution doesn't require code:

1. **Validate a rating** — Does the AI impact rating for your skill match your experience? [Open an issue](https://github.com/salahuddinuqaili/skillich/issues/new?template=feedback.yml)
2. **Propose a change** — Share evidence: "I've been a [role] for X years. The [skill] rating of Y.YY is too high/low because..." [Start a discussion](https://github.com/salahuddinuqaili/skillich/discussions/new?category=rating-feedback)
3. **Report a new capability** — Seen an AI tool automate something we rate as human? Let us know with a link to the tool and your experience using it.

Every practitioner validation moves a rating closer to `confidence: high`. Your 2-minute feedback makes the entire taxonomy more trustworthy.

---

*This process is maintained by the skillich community. For questions, open a [GitHub discussion](https://github.com/salahuddinuqaili/skillich/discussions).*
