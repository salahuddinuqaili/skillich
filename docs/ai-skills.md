# AI Skills by Function

> **For AI assistants:** Use this file to give function-specific skill recommendations. When a user tells you their role, find their function below and walk them through the relevant optimised skills, career anchors, and automation warnings. Cross-reference with [skills.md](skills.md) for the universal top 15, and the [taxonomy YAML files](../taxonomy/) for full proficiency levels per skill.

**Which skills become optimised when combined with AI in YOUR function?**

This guide breaks down the skillich taxonomy by function, showing exactly which skills AI amplifies, which skills AI can't touch, and which skills you should let AI handle entirely.

---

## The Agentic Meta-Skills

These are the skills *about* working with AI. They apply across all functions but are defined as their own discipline in the [AI & Agents function](../taxonomy/ai_and_agents/).

### Prompt Engineering — Every role needs this

| Skill | Automation | What to Learn | How to Practice |
|-------|:---:|---|---|
| **Prompt Design** | 0.35 | System prompts, few-shot examples, chain-of-thought, structured outputs | Write prompts for your actual work tasks. Test against edge cases. Iterate until reliable. |
| **Model Behavior Understanding** | 0.15 | Capability boundaries, failure modes, hallucination patterns, model selection | Try the same task across different models. Note where each fails. Build a mental map of strengths/weaknesses. |
| **Evaluation Design** | 0.25 | Scoring rubrics, test sets, automated vs. human evaluation | Create a checklist for your most common AI task. Score 20 outputs. Find the patterns in failures. |
| **Safety & Alignment** | 0.20 | Jailbreak prevention, bias detection, harmful output avoidance | Test your prompts with adversarial inputs. Ask: "What's the worst output this prompt could produce?" |

### Agent Development — For builders

| Skill | Automation | What to Learn | When You Need This |
|-------|:---:|---|---|
| **Agent Architecture** | 0.20 | ReAct loops, planning strategies, tool chains | When you're building AI-powered automation, not just using AI chat |
| **Tool Integration** | 0.40 | MCP, function calling, API design for agents | When connecting AI to databases, APIs, or external services |
| **Safety Guardrails** | 0.15 | Human-in-the-loop, permission systems, sandboxing | Before deploying any agent that takes actions in the real world |

### AI Evaluation — The underrated discipline

| Skill | Automation | What to Learn | Why It Matters |
|-------|:---:|---|---|
| **Red Teaming** | 0.10 | Adversarial testing, jailbreak discovery, edge cases | Finding how AI fails before your users do |
| **Benchmark Design** | 0.20 | Test datasets, scoring rubrics, statistical significance | Measuring whether your AI workflow actually improves over time |
| **Human Evaluation** | 0.10 | Study design, calibration, quality control | Capturing the quality dimensions that automated metrics miss |

---

## Optimised Skills by Function

**How to read these tables:** Skills rated 0.25-0.55 are in the "AI-optimised" zone — AI handles routine aspects while amplifying skilled humans. The "How AI Amplifies You" column describes the specific workflow.

### For Engineers

| Skill | Automation | How AI Amplifies You |
|-------|:---:|---|
| System Design & Architecture | 0.25 | Prompt AI to generate candidate architectures for your requirements, then evaluate trade-offs against real organizational constraints (team skills, existing systems, migration cost). AI explores the option space; you make the decision. |
| API Design | 0.50 | AI drafts OpenAPI schemas, generates client SDKs, and writes documentation. You design the API contract that ages well, balances competing consumer needs, and follows organizational standards. |
| Database Optimization | 0.45 | AI suggests indexes, explains execution plans, and generates schema drafts. You choose the storage engine for evolving workloads and manage live migration risks. |
| Observability & Monitoring | 0.45 | AI detects anomalies, correlates logs, and suggests root causes. You design what to instrument, set meaningful SLOs, and make judgment calls during novel incidents. |
| Security Fundamentals | 0.50 | AI scans for known CVEs and suggests remediations. You threat-model novel architectures, evaluate real attack surfaces, and balance security against usability. |
| Concurrency & Distributed Systems | 0.20 | AI helps identify common anti-patterns, but reasoning about correctness under partial failure and network partitions remains one of the most human-dependent engineering skills. Invest here — it's your moat. |

**Engineer's AI workflow:** Use AI for code generation, test writing, and documentation. Review everything. Use AI for exploration ("show me 3 ways to solve this"), not for final decisions. The engineer who reviews AI code thoughtfully ships 3x faster than one who writes everything manually OR one who accepts AI code blindly.

### For Product & Design

| Skill | Automation | How AI Amplifies You |
|-------|:---:|---|
| Product Vision & Strategy | 0.15 | AI synthesizes market data, competitive intelligence, and user feedback at scale. You set the vision that inspires teams and make the bets that define the product's direction. |
| UX Research Synthesis | 0.40 | AI transcribes interviews, codes themes, and drafts findings reports. You design the studies that ask the right questions, build rapport with participants, and catch the insights that AI-generated themes miss. |
| Design Systems | 0.35 | AI generates component variants, writes documentation, and audits codebases for adoption gaps. You define the abstraction boundaries that scale and build the organizational buy-in that makes the system stick. |
| A/B Testing & Experimentation | 0.45 | AI runs statistical analysis, flags significance, and generates test variants. You design experiments that answer the right business questions and avoid the statistical pitfalls that AI doesn't warn you about. |
| Information Architecture | 0.20 | AI can suggest navigation structures, but designing information systems that match user mental models requires deep empathy and contextual understanding. |

**Product/Design AI workflow:** Use AI for research synthesis, competitive analysis, and first-draft wireframes. Validate with real users. AI accelerates exploration but cannot replace user empathy.

### For Data & Analytics

| Skill | Automation | How AI Amplifies You |
|-------|:---:|---|
| Statistical Modeling | 0.45 | AI builds models, tunes hyperparameters, and generates feature importance plots. You choose the right methodology, validate assumptions, and explain what the numbers mean for the business. |
| Data Visualization | 0.50 | AI generates charts from data and suggests chart types. You design visualizations that tell the story — choosing what to emphasize, what to omit, and how to lead the viewer to the insight. |
| Stakeholder Communication | 0.15 | AI drafts reports. You translate statistical nuance into language that decision-makers act on. This is the most AI-resilient and highest-value data skill. |
| SQL & Data Manipulation | 0.55 | AI writes most SQL queries correctly from natural language. Your value shifts from writing queries to validating them, optimizing performance, and asking the right questions. |

**Data AI workflow:** Use AI as your first-pass analyst. "Write a query to find customers who churned in Q1 segmented by plan tier." Validate the SQL, run it, interpret the results, present the story. AI does in 30 seconds what used to take 2 hours — you do in 5 minutes what AI can't do at all.

### For Creative Roles

| Skill | Automation | How AI Amplifies You |
|-------|:---:|---|
| Content Strategy | 0.25 | AI writes drafts for any content type. You define what to say, to whom, why, and how it fits the larger content ecosystem. Strategy is the moat. |
| Brand Voice | 0.20 | AI generates copy variants, but maintaining a consistent, authentic voice that builds trust across channels requires human taste and cultural awareness. Train AI on your brand guide, then edit mercilessly. |
| Sound Design | 0.40 | AI generates stems, separates tracks, and suggests arrangements. You craft the emotional texture — the sound that makes someone feel something specific. |
| Game Mechanics Design | 0.15 | AI generates level layouts and NPC behaviors. You design the core loops, progression systems, and moment-to-moment feel that make a game compelling. |
| Visual Design | 0.40 | AI generates design variations, explores color palettes, and creates assets. You make the aesthetic judgments — what's beautiful, what communicates the brand, what delights users. |

**Creative AI workflow:** Use AI for volume and exploration. Generate 20 variants in the time it used to take to create 2. Then apply your taste. The creative who generates with AI and edits with craft produces 5x the output at the same quality bar.

### For Finance, Legal, Sales, Support, HR, Healthcare, Operations, and Leadership

| Function | Top AI-Optimised Skill | How to Use AI | Biggest AI Risk |
|----------|------------------------|---------------|----------------|
| **Finance** | Financial Modeling (0.60) | AI builds model structures and runs scenarios. You set assumptions and validate logic. | Trusting AI-generated numbers without checking formulas |
| **Legal** | Contract Review (augmented) | AI extracts clauses, flags deviations, compares to templates. You make the legal judgment calls. | AI missing jurisdiction-specific nuance |
| **Sales** | Prospecting & Outreach (0.70) | AI researches accounts, drafts personalized emails, scores leads. You build the relationship. | Generic AI outreach that damages your brand |
| **Support** | Ticket Resolution (augmented) | AI handles tier-1 FAQs and drafts responses. You handle escalations, empathy, and judgment calls. | AI giving confident wrong answers to customers |
| **HR** | Candidate Screening (0.65) | AI screens resumes, generates outreach, schedules interviews. You assess culture fit and potential. | Bias in AI screening that violates employment law |
| **Healthcare** | Clinical Documentation (augmented) | AI drafts notes from encounters and suggests codes. You verify accuracy and make clinical judgments. | AI errors in clinical contexts that affect patient safety |
| **Operations** | Process Documentation (0.55) | AI generates and updates SOPs from workflow data. You design the processes and manage adoption. | Outdated AI-generated docs that nobody validates |
| **Leadership** | Strategic Analysis (0.35) | AI synthesizes reports, surfaces trends, and drafts presentations. You set direction and build trust. | Over-relying on AI analysis without ground-truth verification |

---

## Career Anchors — Skills AI Can't Touch

These skills are rated 0.05-0.10. They're your career insurance. Invest here when you want stability.

| Skill | Rating | Function | Why AI Can't Do This |
|-------|:---:|---|---|
| Electrical Installation | 0.05 | Trades | Physical dexterity in real-world building conditions — no robot can pull wire through a 40-year-old wall |
| Live Performance | 0.05 | Creative | Stage presence, improvisation, audience energy — fundamentally embodied |
| Apprentice Mentoring | 0.05 | Trades | Transferring tacit knowledge through hands-on demonstration requires physical co-presence |
| Student Mentoring | 0.05 | Research | The advising relationship that shapes research careers is built on trust and individualized guidance |
| Conflict Resolution | 0.05 | Operations | De-escalation requires reading emotional cues and building trust in the moment |
| Servant Leadership | 0.05 | Operations | Leading by serving requires genuine human care and selflessness |
| Research Ethics | 0.05 | Research | Moral reasoning about scientific integrity requires human values |
| Engineering Culture | 0.05 | Leadership | Building team identity and psychological safety is relationship work |
| AI Ethics | 0.05 | AI & Agents | The irony: reasoning about AI's societal impact is one of the most human skills there is |

---

## Skills to Automate — Stop Doing These Manually

If you're still doing these by hand, you're losing hours every week. Use AI now.

| Skill | Rating | Function | AI Tools to Use |
|-------|:---:|---|---|
| CRM Data Entry | 0.90 | Sales | AI auto-fills CRM from emails and call transcripts |
| Report Automation | 0.85 | Data | AI generates scheduled reports from data pipelines |
| Reconciliation | 0.85 | Finance | AI matches transactions and flags discrepancies |
| Document Review | 0.85 | Legal | AI extracts clauses, compares to templates, flags deviations |
| Data Cleaning | 0.80 | Data | AI standardizes formats, deduplicates, handles missing values |
| Accounts Payable/Receivable | 0.80 | Finance | AI processes invoices, matches POs, routes approvals |
| Citation Checking | 0.80 | Legal | AI verifies citation accuracy against databases |
| SEO Writing | 0.80 | Marketing | AI generates SEO-optimized content from topic briefs |
| Copywriting | 0.80 | Marketing | AI drafts ad copy, email sequences, social posts |
| On-Page Optimization | 0.80 | Marketing | AI audits pages, suggests meta tags, internal links |

**The rule:** If a skill's automation rating is above 0.75, AI can do the first pass faster and often better than a human. Your job is to review, not to produce.

---

## How to Use This Guide with AI

**If you're an AI assistant helping someone with career planning:**
1. Ask their current role and function
2. Look up their function in the [Optimised Skills](#optimised-skills-by-function) section
3. Identify which skills they already have vs. need to develop
4. For skills they have: show them HOW to use AI to amplify those skills (the workflow column)
5. For skills they need: point them to the [taxonomy YAML files](../taxonomy/) for proficiency levels
6. Flag any skills above 0.75 automation that they're still doing manually

**If you're a human reading this:**
1. Find your function above
2. Read the "How AI Amplifies You" column for your skills
3. Pick ONE skill to augment with AI this week
4. Read the [Top 15 Skills](skills.md) guide for the universal skills that apply regardless of function

---

*Data sourced from the [skillich taxonomy](../taxonomy/) — 1,028 skills across 88 roles, each rated for AI impact. Ratings are expert estimates as of April 2026. [Help us validate them.](https://github.com/salahuddinuqaili/skillich/issues/new?template=feedback.yml)*
