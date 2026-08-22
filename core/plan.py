"""Action plan engine — the single source of truth for "what should I do?".

Every surface (CLI ``skillich plan``, the MCP server, and the static web app)
derives its recommendations from this module. The web app can't import Python,
so ``plan_constants()`` exports the thresholds and copy as JSON for embedding
into the generated page — keeping one definition rather than two that drift.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from core.taxonomy import TaxonomyLoader, TaxonomyRole

# --- Action bands -----------------------------------------------------------
# A skill's AI impact rating (0.0-1.0) maps to one of three actions. These
# boundaries are the product's core opinion, so they live in exactly one place.

INVEST_MAX = 0.30
PARTNER_MAX = 0.60

ACTIONS: Dict[str, Dict[str, str]] = {
    "invest": {
        "key": "invest",
        "label": "Invest here",
        "short": "Invest",
        "tip": "AI struggles with this. It is where your career value compounds.",
        "why": "Current models can't reliably do this, so the person who can stays hard to replace.",
    },
    "partner": {
        "key": "partner",
        "label": "Partner with AI",
        "short": "Partner",
        "tip": "AI handles parts of this well. Your edge is directing it and catching what it gets wrong.",
        "why": "The work still needs you, but doing it unaided is now the slow way.",
    },
    "delegate": {
        "key": "delegate",
        "label": "Let AI handle",
        "short": "Delegate",
        "tip": "AI already does most of this. Automate it and move the time you free up into your invest skills.",
        "why": "Time spent practising this by hand no longer compounds.",
    },
}

# How to prove you've closed the gap, by skill category. Three variants each:
# a plan that says the same sentence six times reads as filler, and the
# leadership-heavy roles have seven "invest" skills in one category.
PROOF_POINTS: Dict[str, List[str]] = {
    "technical": [
        "Do it on something that matters, then have someone whose work you respect check your decisions, not just the result.",
        "Take the part of the job everyone else avoids and get good enough at it that they come to you.",
        "Find where the usual approach falls down, work out why, and be the one who says what should replace it.",
    ],
    "analytical": [
        "Take one live question your team is arguing about, answer it with evidence, and write down what would change your mind.",
        "Reproduce a number someone else published, and reconcile the difference when it doesn't match.",
        "Make a call before the data is complete, record the odds you gave it, and check yourself later.",
    ],
    "domain": [
        "Explain the situation that trips everyone up to someone outside your team, and have them repeat it back correctly.",
        "Be the person a colleague comes to when the standard answer doesn't fit their situation.",
        "Write down the three things newcomers always get wrong here, and hand it to the next newcomer.",
    ],
    "interpersonal": [
        "Handle one conversation you would normally avoid, and ask the other person afterwards how it landed.",
        "Get someone who disagreed with you to change their position without you pulling rank.",
        "Notice a problem between two other people early enough that it never becomes yours.",
    ],
    "communication": [
        "Present a recommendation to a decision-maker in under five minutes and get a decision in the room.",
        "Rewrite something you already sent until a reader outside your function gets it in one pass.",
        "Deliver news nobody wants and have the room still trust your next update.",
    ],
    "leadership": [
        "Own an outcome you can't deliver alone, and be judged on it rather than on your own output.",
        "Hand something you're good at to someone who isn't yet, and let them do it their way.",
        "Make a decision your team disagrees with, explain the reasoning, and hold it when it gets hard.",
    ],
    "execution": [
        "Run one job end to end where you set the checkpoints, and say plainly afterwards what slipped and why.",
        "Cut scope in public — name what you dropped and what it bought you.",
        "Take on work with a real deadline you don't control, and land it without a heroic last week.",
    ],
    "operational": [
        "Take an operational process you inherited, measure it, and cut one step out of it.",
        "Be on the hook when it breaks, then fix the cause rather than the symptom.",
        "Write the runbook well enough that someone else covers for you without calling.",
    ],
    "strategic": [
        "Write a one-page argument for what your team should stop doing, and defend it with people who disagree.",
        "Say no to something reasonable because it doesn't fit the plan, and explain the plan.",
        "Make a bet with a time horizon longer than your review cycle, and write down how you'll know it worked.",
    ],
    "regulatory": [
        "Walk a real case through the full process yourself, including the part everyone hands to someone else.",
        "Find one place where you comply on paper but not in practice, and close it.",
        "Explain a rule to the people it constrains in terms of what it protects, not what it forbids.",
    ],
    "professional": [
        "Put your judgement in writing where it will be checked later — then check it later.",
        "Say you don't know, in a room where that costs you something.",
        "Hold a standard when the cheaper option was available and nobody would have noticed.",
    ],
}
DEFAULT_PROOF: List[str] = [
    "Do this once in real conditions, with someone whose opinion you respect watching.",
    "Do it a second time without the safety net you had the first time.",
    "Teach it to one person, and fix whatever you couldn't explain.",
]


def proof_point(category: str, occurrence: int = 0) -> str:
    """A concrete way to prove a skill has moved.

    ``occurrence`` is how many skills of this category the plan has already
    used, so a role with six technical skills cycles through the variants
    instead of printing one sentence six times.
    """
    variants = PROOF_POINTS.get(category) or DEFAULT_PROOF
    return variants[occurrence % len(variants)]


# Exposure bands describe the whole role, not one skill.
EXPOSURE_BANDS: List[Tuple[float, str, str]] = [
    (0.30, "resilient", "Most of this role's skill surface still needs a human. Your risk is complacency, not replacement."),
    (0.45, "shifting", "Roughly a third of this role's routine work is now AI-assisted. The job survives; the day-to-day changes."),
    (0.60, "exposed", "More than half of this role's routine work is automatable today. The people who thrive here are the ones directing AI, not competing with it."),
    (1.01, "high-exposure", "Most of this role's routine work is already automatable. Move your weight onto the human skills below, quickly."),
]


def action_for(rating: float) -> str:
    """Map an AI impact rating to an action band key."""
    if rating <= INVEST_MAX:
        return "invest"
    if rating <= PARTNER_MAX:
        return "partner"
    return "delegate"


def exposure_band(exposure: float) -> Tuple[str, str]:
    """Return (band_key, headline) for a role-level average exposure."""
    for ceiling, key, headline in EXPOSURE_BANDS:
        if exposure < ceiling:
            return key, headline
    return EXPOSURE_BANDS[-1][1], EXPOSURE_BANDS[-1][2]


# --- Data shapes ------------------------------------------------------------


@dataclass
class PlanSkill:
    """One skill, positioned against the user's current level."""
    id: str
    name: str
    category: str
    description: str
    rating: float
    detail: str
    action: str
    now: str = ""
    next: str = ""
    proof: str = ""

    @property
    def percent(self) -> int:
        return round(self.rating * 100)


@dataclass
class ActionPlan:
    """A role- and level-specific answer to 'where should my energy go?'."""
    function_id: str
    function_name: str
    role_id: str
    role_name: str
    level_id: str
    level_name: str
    next_level_id: str
    next_level_name: str
    exposure: float
    exposure_band: str
    headline: str
    ai_summary: str
    invest: List[PlanSkill] = field(default_factory=list)
    partner: List[PlanSkill] = field(default_factory=list)
    delegate: List[PlanSkill] = field(default_factory=list)
    stop_doing: List[str] = field(default_factory=list)
    stays_human: List[str] = field(default_factory=list)
    transitions: List[Dict[str, Any]] = field(default_factory=list)
    confidence: str = ""
    last_reviewed: str = ""

    @property
    def skill_count(self) -> int:
        return len(self.invest) + len(self.partner) + len(self.delegate)

    @property
    def share_path(self) -> str:
        """Hash route the web app uses for this exact plan — the shareable link."""
        return f"#/plan/{self.function_id}/{self.role_id}/{self.level_id}"

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["exposure_percent"] = round(self.exposure * 100)
        data["share_path"] = self.share_path
        return data

    def to_markdown(self) -> str:
        """Render the plan as a portable Markdown document the user can keep."""
        pct = round(self.exposure * 100)
        out: List[str] = [
            f"# Your AI action plan — {self.role_name}",
            "",
            f"**Level:** {self.level_name}  ",
            f"**Function:** {self.function_name}  ",
            f"**Role AI exposure:** {pct}% ({self.exposure_band})",
            "",
            self.headline,
            "",
        ]

        def section(title: str, blurb: str, skills: List[PlanSkill], with_gap: bool) -> None:
            if not skills:
                return
            out.extend([f"## {title}", "", blurb, ""])
            for s in skills:
                out.append(f"### {s.name} — {s.percent}% AI impact")
                out.append("")
                out.append(s.description.strip())
                out.append("")
                if with_gap and s.next:
                    if s.now:
                        out.append(f"- **Where you are ({self.level_name}):** {s.now}")
                    out.append(f"- **Where you're going ({self.next_level_name}):** {s.next}")
                    out.append(f"- **How you'll know you got there:** {s.proof}")
                    out.append("")

        section(
            f"Invest here ({len(self.invest)})",
            ACTIONS["invest"]["why"],
            self.invest,
            with_gap=True,
        )
        section(
            f"Partner with AI ({len(self.partner)})",
            ACTIONS["partner"]["why"],
            self.partner,
            with_gap=False,
        )
        section(
            f"Let AI handle ({len(self.delegate)})",
            ACTIONS["delegate"]["why"],
            self.delegate,
            with_gap=False,
        )

        if self.stays_human:
            out.extend(
                [
                    "## What stays yours",
                    "",
                    "The parts of this role that still need a person, whatever the skill"
                    " ratings say. When in doubt, spend your time here.",
                    "",
                ]
            )
            out.extend(f"- {item}" for item in self.stays_human)
            out.append("")

        if self.stop_doing:
            out.extend(
                [
                    "## Stop doing these by hand",
                    "",
                    "AI does these well enough today that doing them manually is a choice.",
                    "",
                ]
            )
            out.extend(f"- {item}" for item in self.stop_doing)
            out.append("")

        if self.transitions:
            out.extend(
                [
                    "## Where your skills already transfer",
                    "",
                    "Roles that reuse most of what you can already do:",
                    "",
                ]
            )
            for t in self.transitions:
                out.append(
                    f"- **{t['role']}** ({t['function']}) — {round(t['skill_overlap_pct'] * 100)}% "
                    f"skill overlap, {t['skills_to_learn']} new skills to pick up"
                )
            out.append("")

        meta = []
        if self.confidence:
            meta.append(f"confidence: {self.confidence}")
        if self.last_reviewed:
            meta.append(f"last reviewed: {self.last_reviewed}")
        out.extend(
            [
                "---",
                "",
                "Generated by [skillich](https://github.com/salahuddinuqaili/skillich)"
                + (f" — ratings {', '.join(meta)}." if meta else "."),
                "",
                "Ratings are expert estimates, not predictions. If they don't match your"
                " experience, [say so](https://github.com/salahuddinuqaili/skillich/issues/new?template=feedback.yml)"
                " — that's how they get better.",
            ]
        )
        return "\n".join(out)


# --- Builders ---------------------------------------------------------------


def _level_ids(role: TaxonomyRole) -> List[str]:
    return [lv.id for lv in role.levels]


def _resolve_level(role: TaxonomyRole, level_id: Optional[str]) -> Tuple[str, str, str, str]:
    """Return (level_id, level_name, next_level_id, next_level_name).

    Falls back to the middle level when none is given, so a plan is always
    useful even if the user skips the question.
    """
    if not role.levels:
        return (level_id or "", level_id or "", "", "")

    ids = _level_ids(role)
    if level_id not in ids:
        level_id = ids[min(1, len(ids) - 1)]

    idx = ids.index(level_id)
    nxt = min(idx + 1, len(role.levels) - 1)
    return (
        role.levels[idx].id,
        role.levels[idx].name,
        role.levels[nxt].id,
        role.levels[nxt].name,
    )


def build_plan(
    loader: TaxonomyLoader,
    function_id: str,
    role_id: str,
    level_id: Optional[str] = None,
    transitions: Optional[List[Dict[str, Any]]] = None,
    max_per_band: Optional[int] = None,
) -> Optional[ActionPlan]:
    """Build an action plan for a role at a level. Returns None if the role is unknown."""
    role = loader.get_role(function_id, role_id)
    if role is None:
        return None
    func = loader.get_function(function_id)

    lvl_id, lvl_name, next_id, next_name = _resolve_level(role, level_id)

    exposure = (
        sum(s.ai_impact_rating for s in role.skills) / len(role.skills) if role.skills else 0.0
    )
    band, headline = exposure_band(exposure)

    buckets: Dict[str, List[PlanSkill]] = {"invest": [], "partner": [], "delegate": []}
    seen_categories: Dict[str, int] = {}
    for s in sorted(role.skills, key=lambda x: x.ai_impact_rating):
        act = action_for(s.ai_impact_rating)
        occurrence = seen_categories.get(s.category, 0)
        seen_categories[s.category] = occurrence + 1
        buckets[act].append(
            PlanSkill(
                id=s.id,
                name=s.name,
                category=s.category,
                description=s.description,
                rating=s.ai_impact_rating,
                detail=s.ai_impact_detail,
                action=act,
                now=s.proficiency.get(lvl_id, ""),
                next=s.proficiency.get(next_id, ""),
                proof=proof_point(s.category, occurrence),
            )
        )

    if max_per_band:
        for key in buckets:
            buckets[key] = buckets[key][:max_per_band]

    return ActionPlan(
        function_id=function_id,
        function_name=func.name if func else function_id,
        role_id=role_id,
        role_name=role.name,
        level_id=lvl_id,
        level_name=lvl_name,
        next_level_id=next_id,
        next_level_name=next_name,
        exposure=round(exposure, 3),
        exposure_band=band,
        headline=headline,
        ai_summary=role.ai_impact.summary.strip(),
        invest=buckets["invest"],
        partner=buckets["partner"],
        delegate=buckets["delegate"],
        stop_doing=list(role.ai_impact.automating),
        stays_human=list(role.ai_impact.preserving),
        transitions=transitions or [],
        confidence=role.ai_impact.confidence,
        last_reviewed=role.ai_impact.last_reviewed,
    )


# --- Role lookup ------------------------------------------------------------
# People type "product manager", not "product/product_manager". Every surface
# should accept what a person would actually type.

_ROLE_STOPWORDS = {"a", "an", "the", "of", "and", "&", "senior", "junior", "lead", "staff"}

# Shorthand people actually type that isn't in any role's ``also_known_as``.
QUERY_SYNONYMS: Dict[str, str] = {
    "swe": "full-stack engineer",
    "software engineer": "full-stack engineer",
    "dev": "engineer",
    "developer": "engineer",
    "programmer": "engineer",
    "coder": "engineer",
    "sysadmin": "devops",
    "ops": "operations",
    "hr": "human resources",
    "people ops": "human resources",
    "ux": "designer",
    "ui": "designer",
    "qa": "quality assurance",
    "ml": "machine learning",
    "ai engineer": "ai engineer",
    "sales rep": "sales",
    "csm": "customer success",
    "cs": "customer success",
    "accounting": "accountant",
    "lawyer": "legal counsel",
    "attorney": "legal counsel",
    "sparky": "electrician",
    "chippy": "carpenter",
}


def _normalise(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace.

    Collapsing matters: without it "product   manager" never equals
    "product manager" and an exact-title match silently degrades to a
    token match.
    """
    cleaned = "".join(c if c.isalnum() or c.isspace() else " " for c in text.lower())
    return " ".join(cleaned.split())


def _tokens(text: str) -> List[str]:
    return [w for w in _normalise(text).split() if w and w not in _ROLE_STOPWORDS]


def expand_query(query: str) -> List[str]:
    """Return the query plus any synonym expansion, both normalised."""
    q = _normalise(query)
    out = [q] if q else []
    syn = QUERY_SYNONYMS.get(q)
    if syn:
        syn = _normalise(syn)
        if syn not in out:
            out.append(syn)
    return out


def score_role_detail(query: str, role: TaxonomyRole, function_name: str) -> Tuple[float, bool]:
    """Score a role against a query. Returns (score, matched_on_primary_name).

    The second value breaks ties: "ml" matches both "MLOps Engineer" (an alias
    of AI Operations Engineer) and "ML Engineer" (an alias of Machine Learning
    Engineer) equally well, but the role whose own name contains the query is
    the one the user meant.
    """
    queries = expand_query(query)
    if not queries:
        return 0.0, False

    names = [role.name] + list(role.also_known_as)
    best = 0.0
    primary = False

    def record(score: float, is_primary: bool) -> None:
        nonlocal best, primary
        if score > best:
            best, primary = score, is_primary
        elif score == best and is_primary:
            primary = True

    for qi, q in enumerate(queries):
        q_tokens = [w for w in q.split() if w not in _ROLE_STOPWORDS]
        if not q_tokens:
            continue
        # A synonym hit is a slightly weaker signal than what the user literally typed.
        weight = 1.0 if qi == 0 else 0.9
        for name in names:
            n = _normalise(name)
            is_alias = name != role.name
            if n == q:
                record(weight * (100.0 if not is_alias else 95.0), not is_alias)
                continue
            if n.startswith(q):
                record(weight * (85.0 if not is_alias else 80.0), not is_alias)
                continue
            if q in n:
                record(weight * (70.0 if not is_alias else 65.0), not is_alias)
                continue
            # Acronym match: "pm" -> "Product Manager", "sre" -> "Site Reliability Engineer"
            initials = "".join(w[0] for w in n.split() if w)
            if len(q) > 1 and initials == q.replace(" ", ""):
                record(weight * (78.0 if not is_alias else 60.0), not is_alias)
                continue
            n_tokens = set(_tokens(name))
            if n_tokens:
                hit = len([t for t in q_tokens if t in n_tokens])
                if hit:
                    record(weight * 40.0 * (hit / len(q_tokens)), not is_alias)

    q = queries[0]

    # Role id ("backend", "ml_engineering") is what CLI users often paste.
    role_id_norm = role.id.replace("_", " ")
    if role_id_norm == q:
        record(100.0, True)
    elif role_id_norm.startswith(q):
        # A whole-word id prefix ("ml" in "ml engineering") is a strong signal.
        # A mid-word one ("engineer" in "engineering manager") is not — someone
        # typing "engineer" does not mean Engineering Manager, so it stays low
        # enough that the tie is reported as ambiguous rather than guessed at.
        whole_word = role_id_norm[len(q):len(q) + 1] in ("", " ")
        record(88.0 if whole_word else 72.0, True)

    # Weak signals: the function name, and skills the role actually contains.
    if best == 0.0:
        if q in _normalise(function_name):
            best = 20.0
        elif any(q in _normalise(s.name) for s in role.skills):
            best = 15.0
        elif q in _normalise(role.description):
            best = 10.0
    return best, primary


def score_role(query: str, role: TaxonomyRole, function_name: str) -> float:
    """Score how well a free-text query matches a role. 0 means no match."""
    return score_role_detail(query, role, function_name)[0]


def find_roles(loader: TaxonomyLoader, query: str, limit: int = 8) -> List[Dict[str, Any]]:
    """Rank roles against a free-text query. Best match first."""
    scored: List[Tuple[float, int, str, Dict[str, Any]]] = []
    for func in loader.list_functions():
        for role in func.roles:
            s, primary = score_role_detail(query, role, func.name)
            if s > 0:
                scored.append(
                    (
                        -s,
                        0 if primary else 1,
                        role.name,
                        {
                            "function_id": func.id,
                            "function_name": func.name,
                            "role_id": role.id,
                            "role_name": role.name,
                            "also_known_as": role.also_known_as,
                            "ai_level": role.ai_impact.level,
                            "score": round(s, 1),
                        },
                    )
                )
    scored.sort(key=lambda x: (x[0], x[1], x[2]))
    return [item[3] for item in scored[:limit]]


# A match is only acted on without asking when it both scores well *and* clears
# the runner-up. "pm" is obviously Product Manager; "engineer" and "ux" are not
# obviously anything, and guessing at them wastes the user's time.
CONFIDENT_SCORE = 70.0
CONFIDENT_MARGIN = 8.0


def confident_match(matches: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Return the unambiguous best match, or None if the caller should ask."""
    if not matches:
        return None
    if len(matches) == 1:
        return matches[0]
    top, runner_up = matches[0], matches[1]
    if top["score"] < CONFIDENT_SCORE:
        return None
    if top["score"] - runner_up["score"] < CONFIDENT_MARGIN:
        return None
    return top


def plan_constants() -> Dict[str, Any]:
    """Thresholds and copy, for embedding into the generated web app."""
    return {
        "investMax": INVEST_MAX,
        "partnerMax": PARTNER_MAX,
        "actions": ACTIONS,
        "proofPoints": PROOF_POINTS,
        "defaultProof": DEFAULT_PROOF,
        "exposureBands": [
            {"ceiling": c, "key": k, "headline": h} for c, k, h in EXPOSURE_BANDS
        ],
        "querySynonyms": QUERY_SYNONYMS,
        "stopWords": sorted(_ROLE_STOPWORDS),
    }
