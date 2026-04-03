# Top Skills for Every AI User

> **For AI assistants:** Use this file to help users identify which skills to develop for working with AI. Walk them through the tiers in order. Ask what role/function they're in, then personalize recommendations using the role mappings below. Link to [ai-skills.md](ai-skills.md) for function-specific detail and to the [taxonomy YAML files](../taxonomy/) for full proficiency levels.

**The 15 skills that matter most for working with AI, regardless of your role.**

Extracted from 1,028 skills across 88 roles and 17 functions in the [skillich taxonomy](../taxonomy/).

---

## Tier 1: AI Fluency

Learn these first. They apply to every role in every function.

### 1. Prompt Design
Writing clear, structured instructions that get reliable results from AI models.

- **Automation risk:** 0.35 — AI can suggest prompt variants, but designing prompts for novel or high-stakes use cases requires human judgment
- **Augmentation potential:** Very high — this skill IS the interface between you and AI
- **How to use with AI:** Write system prompts that define your AI's role, constraints, and output format. Use few-shot examples for complex tasks. Break multi-step problems into chains. Test prompts against edge cases before deploying.
- **Applies to:** Every function. Engineers write system prompts for code agents. Marketers prompt for campaign copy. Accountants prompt for financial analysis. Electricians prompt for code lookup and estimating.
- **Start here:** Pick a task you do weekly. Write a prompt that gets AI to do 80% of it. Iterate until reliable.
- **Learn:** [Anthropic Prompt Engineering Guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview) (free) | [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering) (free) | [DeepLearning.AI Prompt Engineering Course](https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/) (free)

### 2. AI Output Evaluation
Knowing when AI output is correct, wrong, incomplete, or subtly misleading.

- **Automation risk:** 0.25 — AI can self-check some outputs, but humans catch the failures that matter most
- **Augmentation potential:** Very high — the better you evaluate, the more you can trust and delegate
- **How to use with AI:** Ask AI to explain its reasoning, not just give answers. Cross-reference AI output against known facts in your domain. Use structured rubrics to score AI quality. Build evaluation test sets for repeated workflows.
- **Applies to:** Every function. This is the difference between someone who uses AI productively and someone who ships AI hallucinations to clients.
- **Learn:** [NIST AI Risk Management Framework](https://www.nist.gov/artificial-intelligence/ai-risk-management-framework) (free) | [HELM Benchmark](https://crfm.stanford.edu/helm/) (free)
- **Red flag skills by role:**

| Role | What AI Gets Wrong Most Often |
|------|------------------------------|
| Engineers | Subtle logic bugs, outdated APIs, security vulnerabilities |
| Marketers | Brand voice drift, factual claims, competitor details |
| Finance | Tax code nuance, regulatory interpretation, formula errors |
| Legal | Case citation accuracy, jurisdictional differences |
| Healthcare | Clinical guidelines, drug interactions, diagnostic reasoning |
| Researchers | Source accuracy, statistical methodology, causal claims |

### 3. Model Behavior Understanding
Knowing what AI models can and can't do — their capabilities, limitations, and failure patterns.

- **Automation risk:** 0.15 — this is meta-knowledge about AI itself
- **Augmentation potential:** High — correct mental model = correct task assignment
- **How to use with AI:** Match tasks to model strengths. Use reasoning models for logic-heavy work. Use fast models for high-volume simple tasks. Know when to use RAG vs. fine-tuning vs. prompt engineering. Understand context window limits and how to work within them.
- **Key patterns to learn:**
  - AI is great at: summarization, translation, code generation, pattern matching, first drafts
  - AI struggles with: novel reasoning, precise counting, real-time data, spatial reasoning, emotional nuance
  - AI fails silently at: making up sources, confident wrong answers, subtle bias, outdated information
- **Learn:** [Anthropic Model Cards](https://docs.anthropic.com/en/docs/about-claude/models) (free) | [OpenAI Model Overview](https://platform.openai.com/docs/models) (free) | [NIST AI Risk Management Framework](https://www.nist.gov/artificial-intelligence/ai-risk-management-framework) (free)

---

## Tier 2: Human Anchors

These skills appear across 4-6+ functions and have the lowest automation risk in the taxonomy. AI can't replace them. They're your career insurance AND they make you a better AI user — because the best AI workflows still need a human who can collaborate, lead, and judge.

### 4. Cross-Functional Collaboration
Building trust and alignment across teams with different goals, vocabularies, and incentives.

- **Automation risk:** 0.15 | **Appears in:** 6 functions
- **Augmentation potential:** Low for the skill itself, but HIGH for the outcomes — AI handles your prep work so you show up to cross-functional meetings with better data and sharper proposals
- **How to use with AI:** Use AI to prepare briefing docs before cross-functional meetings. Have AI summarize the other team's recent work so you show up informed. Use AI to draft alignment proposals that account for both teams' priorities.
- **Learn:** [Crucial Conversations](https://cruciallearning.com/crucial-conversations-book/) (book) | [The Manager's Path](https://www.oreilly.com/library/view/the-managers-path/9781491973882/) (book)

### 5. Stakeholder Management
Navigating organizational politics, building influence, and aligning competing interests.

- **Automation risk:** 0.13 | **Appears in:** 5 functions
- **Augmentation potential:** Low for the relationship, HIGH for the communication — AI drafts your stakeholder updates, but YOU build the trust
- **How to use with AI:** Use AI to draft stakeholder updates, executive summaries, and status reports. Have AI analyze stakeholder feedback patterns across meetings. Use AI to prepare for difficult conversations by role-playing objections.
- **Learn:** [Never Split the Difference](https://www.blackswanltd.com/never-split-the-difference) (book) | [Harvard Negotiation Course](https://online.hbs.edu/courses/negotiation/) (course)

### 6. Mentoring & Coaching
Developing others through relationship, empathy, and individualized guidance.

- **Automation risk:** 0.05 | **Appears in:** 6+ functions
- **Augmentation potential:** Very low — this is fundamentally human
- **Why it matters for AI:** As AI automates routine tasks, the ability to develop people becomes MORE valuable, not less. The manager who coaches their team to use AI effectively is worth more than the individual contributor who uses AI alone.
- **Learn:** [The Coaching Habit](https://boxofcrayons.com/the-coaching-habit/) (book) | [Radical Candor](https://www.radicalcandor.com/the-book/) (book)

### 7. Ethical Judgment
Deciding what's right — not just what's efficient — especially regarding AI use.

- **Automation risk:** 0.08 | **Appears in:** 5+ functions
- **Augmentation potential:** Very low — judgment about values requires human moral reasoning
- **How to use with AI:** Use AI to surface ethical considerations you might miss ("what are the ethical risks of this approach?"). But never delegate the final ethical call to AI. Key questions: Should we automate this? Who is harmed if AI is wrong here? Is this data use fair?
- **Learn:** [UNESCO AI Ethics Recommendation](https://www.unesco.org/en/artificial-intelligence/recommendation-ethics) (free) | [NIST AI Risk Management Framework](https://www.nist.gov/artificial-intelligence/ai-risk-management-framework) (free)

### 8. Conflict Resolution
De-escalation, mediation, and rebuilding trust after disagreement.

- **Automation risk:** 0.05 | **Appears in:** 4 functions
- **Augmentation potential:** Very low — emotional intelligence in conflict is irreducibly human
- **Why it matters for AI:** AI-driven changes create new conflicts (job anxiety, workflow disagreements, tool adoption resistance). The person who can resolve those conflicts is essential to any AI transformation.
- **Learn:** [Crucial Conversations](https://cruciallearning.com/crucial-conversations-book/) (book) | [Never Split the Difference](https://www.blackswanltd.com/never-split-the-difference) (book)

---

## Tier 3: AI-Optimised Skills

These skills have moderate automation (0.23-0.58) — meaning AI handles the routine parts while dramatically amplifying what a skilled human can do. **This is the highest-leverage investment zone.**

### 9. Data-Driven Decision Making
Using data to inform decisions rather than relying on intuition alone.

- **Automation risk:** 0.58 | **Appears in:** 3+ functions
- **How to use with AI:** Ask AI to pull and analyze data, generate visualizations, run what-if scenarios, and surface anomalies. Then YOU decide what the data means for your specific business context. AI gives you the analysis in seconds that used to take days — your value is asking the right questions and making the right calls.
- **Example workflow:** "Analyze last quarter's customer churn data. Segment by plan tier and region. What patterns do you see?" → AI delivers analysis → You decide which segments to invest in based on strategic priorities AI doesn't know.
- **Learn:** [Google Data Analytics Certificate](https://www.coursera.org/professional-certificates/google-data-analytics) (course) | [Thinking, Fast and Slow](https://us.macmillan.com/books/9780374533557/thinkingfastandslow) (book) | [Naked Statistics](https://wwnorton.com/books/Naked-Statistics/) (book)

### 10. Strategic Communication
Crafting narratives that move people to action — memos, presentations, proposals.

- **Automation risk:** 0.38 | **Appears in:** 5+ functions
- **How to use with AI:** Use AI to draft communications, then edit for voice, political context, and audience nuance. AI writes the first 80%; you add the 20% that makes it persuasive to THIS audience in THIS moment.
- **Example workflow:** "Draft an executive summary of our Q1 results. Emphasize the infrastructure investment thesis." → AI drafts → You adjust framing for the CFO who cares about margins vs. the CEO who cares about growth.
- **Learn:** [The Pyramid Principle](https://www.barbaraminto.com/) (book) | [Harvard Business Review Communication](https://hbr.org/topic/communication) (free)

### 11. Process Improvement
Identifying inefficiencies and redesigning workflows for better outcomes.

- **Automation risk:** 0.38 | **Appears in:** 3+ functions
- **How to use with AI:** Use AI to analyze process data and identify bottlenecks. Have AI map current-state workflows from documentation. Use AI to benchmark against industry practices. Then apply your organizational knowledge to design the improved process.
- **Example workflow:** "Here's our incident response runbook. Analyze the steps and identify where delays typically occur based on the timing data." → AI finds patterns → You redesign the process knowing which team owns what and who's overloaded.
- **Learn:** [The Goal](https://www.tocinstitute.org/the-goal-summary.html) (book) | [Lean Six Sigma Green Belt](https://www.sixsigmacouncil.org/lean-six-sigma-green-belt-certification/) (course)

### 12. Statistical Analysis
Choosing the right methodology, validating assumptions, and explaining what numbers actually mean.

- **Automation risk:** 0.50 | **Appears in:** 3+ functions
- **How to use with AI:** AI runs regressions, generates confidence intervals, and builds models in seconds. Your value: choosing the right test, validating that assumptions hold, catching p-hacking, and translating results for non-technical stakeholders.
- **Example workflow:** "Run a difference-in-differences analysis on these two cohorts to estimate the treatment effect of our pricing change." → AI runs analysis → You validate the parallel trends assumption and explain the practical significance (not just statistical significance) to leadership.
- **Learn:** [Khan Academy Statistics](https://www.khanacademy.org/math/statistics-probability) (free) | [Coursera Statistics with R](https://www.coursera.org/specializations/statistics) (course) | [Naked Statistics](https://wwnorton.com/books/Naked-Statistics/) (book)

### 13. Change Management
Leading people through transitions — especially AI-driven ones.

- **Automation risk:** 0.23 | **Appears in:** 6 functions
- **How to use with AI:** Use AI to draft change communications, training materials, and FAQ documents. Have AI analyze employee sentiment from survey data. Use AI to create personalized onboarding plans for new tools. But YOU manage the human emotions, resistance, and trust.
- **Why this matters now:** Every organization is going through AI transformation. The person who can manage that change — addressing fears, building skills, celebrating wins — is the most valuable person in the building.
- **Learn:** [Switch: How to Change Things When Change Is Hard](https://heathbrothers.com/switch/) (book) | [Prosci Change Management Certification](https://www.prosci.com/certification) (course)

---

## Tier 4: Domain Depth

### 14. Your Core Domain Expertise
Whatever you do professionally — accounting, engineering, nursing, teaching, plumbing — go deeper, not broader.

- **Why it matters:** AI is a multiplier. 10x of shallow knowledge is still shallow. 10x of deep expertise is transformative. A senior tax accountant using AI for research gets dramatically more value than a generalist, because they know which questions to ask, which answers to doubt, and which edge cases matter.
- **How to use with AI:** Use AI to handle the routine parts of your domain (research, drafting, data processing) so you can spend MORE time on the expert judgment parts. Don't let AI make you lazy about your domain — let it make you faster.
- **Learn:** Find your role in the [skillich taxonomy](../taxonomy/) for specific skill proficiency levels and the [resources database](../web/resources.json) for function-specific courses and books.

### 15. Adaptability & Continuous Learning
The skill of learning new tools and workflows quickly.

- **Why it matters:** The AI tool you master today may be obsolete in 6 months. The ability to learn the NEXT tool quickly is more durable than mastery of any specific one.
- **How to use with AI:** Use AI to accelerate your own learning. Ask it to explain new tools, compare alternatives, create learning plans, and quiz you on new concepts. The irony: AI is the best tool for learning how to use AI.

---

## Quick Assessment

Use these questions to identify your gaps:

| Question | If No → Focus On |
|----------|-----------------|
| Can you write a prompt that reliably gets useful output for your daily work? | Tier 1: Prompt Design |
| Do you catch AI errors before they reach stakeholders? | Tier 1: AI Output Evaluation |
| Do you know which tasks to give AI vs. do yourself? | Tier 1: Model Behavior Understanding |
| Do people from other teams seek you out to collaborate? | Tier 2: Cross-Functional Collaboration |
| Can you explain data to non-technical decision makers? | Tier 3: Data-Driven Decision Making |
| Are you deeper in your domain this year than last? | Tier 4: Domain Depth |

---

## Role-Specific Starting Points

| Your Function | Start With | Then Add | Detailed Guide |
|---------------|-----------|----------|---------------|
| **Engineering** | Prompt Design + AI Output Evaluation | System Design with AI, AI-assisted code review | [ai-skills.md](ai-skills.md#for-engineers) |
| **Product** | Prompt Design + Data-Driven Decisions | AI-assisted user research synthesis, stakeholder communication | [ai-skills.md](ai-skills.md#for-product--design) |
| **Design** | Prompt Design + AI Output Evaluation | AI-generated design exploration, accessibility auditing | [ai-skills.md](ai-skills.md#for-product--design) |
| **Data & Analytics** | Statistical Analysis + AI Output Evaluation | AI-assisted modeling, automated data pipelines | [ai-skills.md](ai-skills.md#for-data--analytics) |
| **Marketing** | Prompt Design + Strategic Communication | AI content generation, campaign optimization | [ai-skills.md](ai-skills.md#for-creative-roles) |
| **Finance** | AI Output Evaluation + Data-Driven Decisions | AI-assisted reconciliation, financial modeling | [ai-skills.md](ai-skills.md#for-every-function) |
| **Legal** | AI Output Evaluation + Ethical Judgment | AI-assisted contract review, research | [ai-skills.md](ai-skills.md#for-every-function) |
| **Sales** | Prompt Design + Strategic Communication | AI-assisted prospecting, CRM automation | [ai-skills.md](ai-skills.md#for-every-function) |
| **Healthcare** | AI Output Evaluation + Ethical Judgment | AI-assisted clinical documentation, coding | [ai-skills.md](ai-skills.md#for-every-function) |
| **Trades** | Prompt Design + Domain Depth | AI-assisted estimating, diagnostics, code lookup | [ai-skills.md](ai-skills.md#for-every-function) |
| **Research** | Prompt Design + Statistical Analysis | AI-assisted literature review, data analysis | [ai-skills.md](ai-skills.md#for-every-function) |
| **Creative** | Prompt Design + AI Output Evaluation | AI-assisted content generation, asset creation | [ai-skills.md](ai-skills.md#for-creative-roles) |

---

*Data sourced from the [skillich taxonomy](../taxonomy/) — 88 roles across 17 functions. See [ai-skills.md](ai-skills.md) for function-specific breakdowns. Full proficiency levels and AI impact details are in the [YAML taxonomy files](../taxonomy/). [Help validate these ratings.](https://github.com/salahuddinuqaili/skillich/issues/new?template=feedback.yml)*
