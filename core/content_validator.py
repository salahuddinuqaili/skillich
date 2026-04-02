"""Content quality validator for taxonomy data.

Goes beyond schema validation to check content quality: thin descriptions,
rating clustering, source coverage, and cross-role consistency.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field

from core.taxonomy import TaxonomyLoader


@dataclass
class ContentIssue:
    """A single content quality issue."""
    severity: str  # "error", "warning", "info"
    category: str  # "thin_content", "rating_quality", "sources", "consistency"
    file: str
    message: str

    def __str__(self) -> str:
        return f"[{self.severity}] {self.file}: {self.message}"


@dataclass
class ContentReport:
    """Result of content quality analysis."""
    issues: list[ContentIssue] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def errors(self) -> list[ContentIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[ContentIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def summary(self) -> str:
        errs = len(self.errors)
        warns = len(self.warnings)
        infos = len([i for i in self.issues if i.severity == "info"])
        return f"{errs} errors, {warns} warnings, {infos} info"


# Thresholds
MIN_PROFICIENCY_CHARS = 120
MIN_SOURCES_PER_ROLE = 2
MAX_RATING_CONCENTRATION = 0.20  # no single rating should be >20% of all ratings in a role


def validate_content(taxonomy_dir: str = "taxonomy") -> ContentReport:
    """Run all content quality checks against the taxonomy."""
    report = ContentReport()
    loader = TaxonomyLoader(taxonomy_dir)

    _check_proficiency_depth(loader, report)
    _check_rating_quality(loader, report)
    _check_source_coverage(loader, report)
    _check_cross_role_consistency(loader, report)
    _compute_stats(loader, report)

    return report


def _check_proficiency_depth(loader: TaxonomyLoader, report: ContentReport) -> None:
    """Flag proficiency descriptions that are too thin to be useful."""
    for func in loader.list_functions():
        for role in loader.list_roles(func.id):
            file_path = f"taxonomy/{func.id}/{role.id}.yaml"
            thin_count = 0
            for skill in role.skills:
                for level_id, desc in skill.proficiency.items():
                    chars = len(desc.strip())
                    if chars < MIN_PROFICIENCY_CHARS:
                        thin_count += 1
                        report.issues.append(ContentIssue(
                            severity="warning",
                            category="thin_content",
                            file=file_path,
                            message=(
                                f"Skill '{skill.name}' level '{level_id}' proficiency "
                                f"is only {chars} chars (min: {MIN_PROFICIENCY_CHARS}). "
                                f"Add observable behaviors, tools, or trade-offs."
                            ),
                        ))
            total_descs = len(role.skills) * len(role.levels)
            if total_descs > 0 and thin_count / total_descs > 0.5:
                report.issues.append(ContentIssue(
                    severity="error",
                    category="thin_content",
                    file=file_path,
                    message=(
                        f"Role has {thin_count}/{total_descs} thin proficiency descriptions "
                        f"({thin_count / total_descs:.0%}). This role needs deepening."
                    ),
                ))


def _check_rating_quality(loader: TaxonomyLoader, report: ContentReport) -> None:
    """Flag rating clustering and lack of differentiation."""
    for func in loader.list_functions():
        for role in loader.list_roles(func.id):
            file_path = f"taxonomy/{func.id}/{role.id}.yaml"
            ratings = [s.ai_impact_rating for s in role.skills]
            if not ratings:
                continue

            counter = Counter(ratings)
            for rating, count in counter.items():
                concentration = count / len(ratings)
                if concentration > MAX_RATING_CONCENTRATION and len(ratings) >= 5:
                    report.issues.append(ContentIssue(
                        severity="warning",
                        category="rating_quality",
                        file=file_path,
                        message=(
                            f"{count}/{len(ratings)} skills ({concentration:.0%}) share "
                            f"rating {rating}. Differentiate ratings to reflect "
                            f"real differences in AI impact."
                        ),
                    ))

            # Check for false precision at 0.5 (the "I don't know" midpoint)
            midpoint_count = counter.get(0.5, 0)
            if midpoint_count >= 3:
                report.issues.append(ContentIssue(
                    severity="warning",
                    category="rating_quality",
                    file=file_path,
                    message=(
                        f"{midpoint_count} skills rated exactly 0.5. "
                        f"The midpoint often signals uncertainty -- consider "
                        f"researching specific AI capabilities for these skills."
                    ),
                ))


def _check_source_coverage(loader: TaxonomyLoader, report: ContentReport) -> None:
    """Flag roles with insufficient source citations."""
    for func in loader.list_functions():
        for role in loader.list_roles(func.id):
            file_path = f"taxonomy/{func.id}/{role.id}.yaml"
            source_count = len(role.ai_impact.sources) if role.ai_impact.sources else 0
            if source_count < MIN_SOURCES_PER_ROLE:
                report.issues.append(ContentIssue(
                    severity="error",
                    category="sources",
                    file=file_path,
                    message=(
                        f"Only {source_count} source(s) cited (min: {MIN_SOURCES_PER_ROLE}). "
                        f"Add research, industry reports, or practitioner references."
                    ),
                ))


def _check_cross_role_consistency(loader: TaxonomyLoader, report: ContentReport) -> None:
    """Flag duplicate skill names with inconsistent ratings across roles."""
    skill_map: dict[str, list[tuple[str, str, float]]] = defaultdict(list)

    for func in loader.list_functions():
        for role in loader.list_roles(func.id):
            for skill in role.skills:
                key = skill.name.lower().strip()
                skill_map[key].append((
                    f"{func.id}/{role.id}",
                    skill.name,
                    skill.ai_impact_rating,
                ))

    for skill_name_lower, occurrences in skill_map.items():
        if len(occurrences) < 2:
            continue

        ratings = [r for _, _, r in occurrences]
        spread = max(ratings) - min(ratings)
        if spread > 0.2:
            locations = ", ".join(f"{loc} ({rating})" for loc, _, rating in occurrences)
            report.issues.append(ContentIssue(
                severity="warning",
                category="consistency",
                file="(multiple)",
                message=(
                    f"Skill '{occurrences[0][1]}' appears in {len(occurrences)} roles "
                    f"with rating spread of {spread:.2f}: {locations}. "
                    f"Consider aligning ratings or explaining the difference."
                ),
            ))


def _compute_stats(loader: TaxonomyLoader, report: ContentReport) -> None:
    """Compute summary statistics for the report."""
    all_ratings = []
    all_prof_lengths = []
    roles_checked = 0

    for func in loader.list_functions():
        for role in loader.list_roles(func.id):
            roles_checked += 1
            for skill in role.skills:
                all_ratings.append(skill.ai_impact_rating)
                for desc in skill.proficiency.values():
                    all_prof_lengths.append(len(desc.strip()))

    report.stats = {
        "roles_checked": roles_checked,
        "total_skills": len(all_ratings),
        "total_proficiency_descriptions": len(all_prof_lengths),
        "avg_proficiency_chars": sum(all_prof_lengths) / len(all_prof_lengths) if all_prof_lengths else 0,
        "min_proficiency_chars": min(all_prof_lengths) if all_prof_lengths else 0,
        "thin_descriptions": sum(1 for length in all_prof_lengths if length < MIN_PROFICIENCY_CHARS),
        "unique_ratings": len(set(all_ratings)),
        "most_common_rating": Counter(all_ratings).most_common(1)[0] if all_ratings else None,
    }
