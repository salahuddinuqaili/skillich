# Contributing to skillich

The most valuable contributions add real, specific knowledge about how AI transforms roles.

## Adding a New Role

1. Create `taxonomy/<function>/<role_id>.yaml` following the schema below.
2. Add the role ID to `taxonomy/<function>/_function.yaml`.
3. Run `python -c "from core.taxonomy import TaxonomyLoader; l = TaxonomyLoader('taxonomy'); print(l.stats)"` to verify it loads.
4. Run `pytest` to ensure nothing breaks.

## Role File Schema

```yaml
role:
  id: role_id              # snake_case, unique within function
  function: function_id    # must match parent directory
  name: "Role Name"
  also_known_as: ["Alias 1", "Alias 2"]
  description: >
    2-3 sentences. What does this person do day-to-day?

  ai_impact:
    level: moderate-high   # low | moderate | moderate-high | high | very-high
    summary: >
      3-4 sentences on how AI is specifically transforming this role.
    automating:            # Tasks AI is absorbing -- be specific
      - "Concrete task description"
    augmenting:            # Tasks where AI makes humans more effective
      - "Concrete task description"
    preserving:            # Tasks that remain fully human
      - "Concrete task description"
    sources:
      - name: "Source Name"
        url: "https://..."

  levels:
    - id: junior           # Always these 5: junior, mid, senior, staff, principal
      name: "Junior (L1-L2)"
      years_experience: "0-2"
      summary: "One sentence describing expectations at this level."
    # ... mid, senior, staff, principal

  skills:
    - id: skill_id         # snake_case
      name: "Skill Name"
      category: technical  # technical | analytical | leadership | communication | domain
      description: "One sentence."
      proficiency:
        junior: "1-2 sentences. Observable behaviors."
        mid: "1-2 sentences."
        senior: "1-2 sentences."
        staff: "1-2 sentences."
        principal: "1-2 sentences."
      ai_impact:
        rating: 0.4        # 0.0 = fully human, 1.0 = fully automatable
        detail: "1-2 sentences explaining the rating."
```

## Quality Standards

- **AI impact ratings must be defensible.** Cite research or industry data where possible.
- **Proficiency descriptions must be observable.** "Understands X" is weak. "Designs X for Y with Z constraints" is strong.
- **Descriptions are for LLM consumption.** Be specific about when to use and when NOT to use each skill.
- **10-12 skills per role.** More is noise, fewer misses critical capabilities.

## What We Need Most

1. **New function categories** -- finance, legal, healthcare, education, creative
2. **Updated AI impact data** -- as models improve, ratings shift
3. **Non-English translations** -- the YAML structure supports this
4. **Real practitioner validation** -- are the proficiency descriptions accurate?
