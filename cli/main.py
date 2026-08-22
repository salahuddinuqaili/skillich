"""skillich CLI -- explore AI impact on tech roles from the terminal."""

import json
from enum import Enum
from pathlib import Path
from typing import Optional

import typer

from cli import formatters
from cli.export import export_csv, export_json
from core.registry import SkillRegistry
from core.taxonomy import TaxonomyLoader

app = typer.Typer(
    name="skillich",
    help="The AI skills transformation guide. Explore roles, analyze AI impact, and plan your career.",
    no_args_is_help=True,
)

_DEFAULT_TAXONOMY = str(Path(__file__).resolve().parent.parent / "taxonomy")


class OutputFormat(str, Enum):
    rich = "rich"
    json = "json"
    csv = "csv"


def _loader(taxonomy_dir: str = _DEFAULT_TAXONOMY) -> TaxonomyLoader:
    return TaxonomyLoader(taxonomy_dir)


def _registry(loader: TaxonomyLoader) -> SkillRegistry:
    from skills.taxonomy_skills.ai_impact_analyzer import AIImpactAnalyzerSkill
    from skills.taxonomy_skills.career_advisor import CareerAdvisorSkill
    from skills.taxonomy_skills.learning_path import LearningPathSkill
    from skills.taxonomy_skills.role_explorer import RoleExplorerSkill
    from skills.taxonomy_skills.skill_assessor import SkillAssessorSkill

    reg = SkillRegistry()
    reg.register(RoleExplorerSkill(loader=loader))
    reg.register(AIImpactAnalyzerSkill(loader=loader))
    reg.register(SkillAssessorSkill(loader=loader))
    reg.register(LearningPathSkill(loader=loader))
    reg.register(CareerAdvisorSkill(loader=loader))
    return reg


def _emit(data: object, fmt: OutputFormat) -> None:
    """Emit result data in the requested format.

    rich: no-op — caller handles output via formatters.
    json: print compact JSON to stdout (no ANSI codes), then exit 0.
    csv:  flat CSV to stdout; falls back to JSON for deeply nested structures.
    """
    if fmt == OutputFormat.json:
        print(json.dumps(data, indent=2, default=str))
        raise typer.Exit(0)
    if fmt == OutputFormat.csv:
        import csv
        import io
        if isinstance(data, list) and data and isinstance(data[0], dict):
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=data[0].keys(), extrasaction="ignore")
            writer.writeheader()
            writer.writerows(data)
            print(buf.getvalue(), end="")
        elif isinstance(data, dict):
            buf = io.StringIO()
            writer = csv.writer(buf)
            for k, v in data.items():
                writer.writerow([k, v if not isinstance(v, (list, dict)) else json.dumps(v)])
            print(buf.getvalue(), end="")
        else:
            print(json.dumps(data, indent=2, default=str))
        raise typer.Exit(0)
    # fmt == rich: caller handles output — nothing to do here


_FMT = typer.Option(OutputFormat.rich, "--format", "-o", help="Output format: rich (default), json, csv")

# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def plan(
    query: Optional[str] = typer.Argument(
        None, help="Your job title, e.g. 'product manager', 'pm', 'electrician'"
    ),
    function_id: Optional[str] = typer.Option(None, "--function", "-f", help="Function ID (skips search)"),
    role_id: Optional[str] = typer.Option(None, "--role", "-r", help="Role ID (skips search)"),
    level: Optional[str] = typer.Option(None, "--level", "-l", help="Your level: junior, mid, senior, staff"),
    show_all: bool = typer.Option(False, "--all", "-a", help="Show every skill, not just the top few"),
    with_transitions: bool = typer.Option(
        False, "--transitions", "-t", help="Include roles your skills transfer to"
    ),
    save: Optional[str] = typer.Option(None, "--save", "-s", help="Write the plan to a Markdown file"),
    fmt: OutputFormat = _FMT,
):
    """Get your personalised AI action plan: what to invest in, partner on, and delegate.

    Type your job title the way you'd say it out loud:

        skillich plan "product manager"
        skillich plan pm --level senior
        skillich plan electrician --save plan.md
    """
    from core.plan import build_plan, confident_match, find_roles

    loader = _loader()

    if not (function_id and role_id):
        if not query:
            query = typer.prompt("What's your job title?")
        matches = find_roles(loader, query, limit=8)
        if not matches:
            formatters.print_error(f"No role matches \"{query}\".")
            formatters.console.print(
                "  Browse what's covered with [cyan]skillich explore[/cyan], or request the role: "
                "https://github.com/salahuddinuqaili/skillich/issues/new"
            )
            raise typer.Exit(1)

        # An unambiguous winner: don't make the user confirm the obvious.
        pick = confident_match(matches)
        if pick is None:
            formatters.print_role_matches(query, matches)
            choice = typer.prompt("Which one? (number)", default="1")
            try:
                pick = matches[int(choice) - 1]
            except (ValueError, IndexError):
                formatters.print_error("Not a valid choice.")
                raise typer.Exit(1)
        function_id, role_id = pick["function_id"], pick["role_id"]

    role = loader.get_role(function_id, role_id)
    if role is None:
        formatters.print_error(f"Role '{role_id}' not found in function '{function_id}'.")
        raise typer.Exit(1)

    if level is None and role.levels:
        if fmt == OutputFormat.rich:
            formatters.console.print(f"\n[bold]{role.name}[/bold] — what's your level?")
            for i, lv in enumerate(role.levels, 1):
                formatters.console.print(f"  [cyan]{i}[/cyan]. {lv.name} [dim]({lv.years_experience} yrs)[/dim]")
            choice = typer.prompt("Level (number)", default="2")
            try:
                level = role.levels[int(choice) - 1].id
            except (ValueError, IndexError):
                level = role.levels[min(1, len(role.levels) - 1)].id
        else:
            level = role.levels[min(1, len(role.levels) - 1)].id

    transitions_data = None
    if with_transitions:
        reg = _registry(loader)
        result = reg.call_skill(
            "career_advisor",
            action="find_transitions",
            source_function_id=function_id,
            source_role_id=role_id,
            limit=5,
        )
        if result.ok:
            transitions_data = result.data["transitions"]

    action_plan = build_plan(loader, function_id, role_id, level, transitions=transitions_data)
    if action_plan is None:
        formatters.print_error("Could not build a plan for that role.")
        raise typer.Exit(1)

    if save:
        Path(save).write_text(action_plan.to_markdown(), encoding="utf-8")

    _emit(action_plan.to_dict(), fmt)

    formatters.print_plan(action_plan, show_all=show_all)
    # soft_wrap keeps the URL and the path on one line so terminals can linkify
    # them and the user can copy them without stitching the halves together.
    formatters.console.print("\n[dim]Share this plan:[/dim]", end=" ")
    formatters.console.print(
        f"[dim]https://salahuddinuqaili.github.io/skillich/{action_plan.share_path}[/dim]",
        soft_wrap=True,
    )
    if save:
        formatters.console.print("[green]Saved to[/green]", end=" ")
        formatters.console.print(f"[green]{save}[/green]", soft_wrap=True)
    else:
        formatters.console.print("[dim]Keep it: rerun with [cyan]--save plan.md[/cyan][/dim]")


@app.command()
def explore(
    function_id: Optional[str] = typer.Option(None, "--function", "-f", help="Function ID, e.g. 'engineering'"),
    role_id: Optional[str] = typer.Option(None, "--role", "-r", help="Role ID, e.g. 'backend'"),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search skills by keyword"),
    fmt: OutputFormat = _FMT,
):
    """Browse functions, roles, and skills in the taxonomy."""
    loader = _loader()
    reg = _registry(loader)

    if search:
        result = reg.call_skill("role_explorer", action="search_skills", query=search)
        if not result.ok:
            formatters.print_error(result.error)
            raise typer.Exit(1)
        _emit(result.data, fmt)
        formatters.print_search_results(search, result.data["skills"], result.data["count"])
    elif function_id and role_id:
        result = reg.call_skill("role_explorer", action="get_role", function_id=function_id, role_id=role_id)
        if not result.ok:
            formatters.print_error(result.error)
            raise typer.Exit(1)
        _emit(result.data, fmt)
        formatters.print_role_detail(result.data)
    elif function_id:
        result = reg.call_skill("role_explorer", action="list_roles", function_id=function_id)
        if not result.ok:
            formatters.print_error(result.error)
            raise typer.Exit(1)
        _emit(result.data, fmt)
        formatters.print_roles(function_id, result.data["roles"])
    else:
        result = reg.call_skill("role_explorer", action="list_functions")
        if not result.ok:
            formatters.print_error(result.error)
            raise typer.Exit(1)
        _emit(result.data, fmt)
        formatters.print_functions(result.data["functions"])


@app.command()
def impact(
    function_id: Optional[str] = typer.Option(None, "--function", "-f", help="Function ID"),
    role_id: Optional[str] = typer.Option(None, "--role", "-r", help="Role ID"),
    compare: bool = typer.Option(False, "--compare", "-c", help="Compare all roles in a function"),
    resilient: bool = typer.Option(False, "--resilient", help="Show most AI-resilient skills"),
    automatable: bool = typer.Option(False, "--automatable", help="Show most automatable skills"),
    limit: int = typer.Option(20, "--limit", "-n", help="Max results"),
    fmt: OutputFormat = _FMT,
):
    """Analyze AI impact on tech roles and skills."""
    loader = _loader()
    reg = _registry(loader)

    if resilient:
        result = reg.call_skill("ai_impact_analyzer", action="most_resilient", limit=limit)
        if not result.ok:
            formatters.print_error(result.error)
            raise typer.Exit(1)
        _emit(result.data, fmt)
        formatters.print_resilient_skills(result.data["skills"])
    elif automatable:
        result = reg.call_skill("ai_impact_analyzer", action="most_automatable", limit=limit)
        if not result.ok:
            formatters.print_error(result.error)
            raise typer.Exit(1)
        _emit(result.data, fmt)
        formatters.print_automatable_skills(result.data["skills"])
    elif compare and function_id:
        result = reg.call_skill("ai_impact_analyzer", action="compare_roles", function_id=function_id)
        if not result.ok:
            formatters.print_error(result.error)
            raise typer.Exit(1)
        _emit(result.data, fmt)
        formatters.print_impact_comparison(result.data)
    elif function_id and role_id:
        result = reg.call_skill(
            "ai_impact_analyzer", action="role_impact", function_id=function_id, role_id=role_id
        )
        if not result.ok:
            formatters.print_error(result.error)
            raise typer.Exit(1)
        _emit(result.data, fmt)
        formatters.print_role_impact(result.data)
    else:
        formatters.print_error(
            "Provide --function and --role for role impact, --compare with --function, "
            "or --resilient / --automatable"
        )
        raise typer.Exit(1)


@app.command()
def assess(
    function_id: str = typer.Option(..., "--function", "-f", help="Target function ID"),
    role_id: str = typer.Option(..., "--role", "-r", help="Target role ID"),
    level: str = typer.Option(..., "--level", "-l", help="Target level: junior/mid/senior/staff/principal"),
    skills_json: str = typer.Option(
        ..., "--skills", "-s",
        help='JSON array: [{"skill_id":"api_design","current_level":"mid"}, ...]',
    ),
    fmt: OutputFormat = _FMT,
):
    """Assess your skills against a target role and identify gaps."""
    loader = _loader()
    reg = _registry(loader)

    try:
        assessments = json.loads(skills_json)
    except json.JSONDecodeError as e:
        formatters.print_error(f"Invalid JSON for --skills: {e}")
        raise typer.Exit(1)

    result = reg.call_skill(
        "skill_assessor",
        function_id=function_id,
        role_id=role_id,
        target_level=level,
        assessments=assessments,
    )
    if not result.ok:
        formatters.print_error(result.error)
        raise typer.Exit(1)
    _emit(result.data, fmt)
    formatters.print_assessment(result.data)


@app.command()
def learn(
    function_id: str = typer.Option(..., "--function", "-f", help="Target function ID"),
    role_id: str = typer.Option(..., "--role", "-r", help="Target role ID"),
    level: str = typer.Option(..., "--level", "-l", help="Target level"),
    from_level: str = typer.Option("junior", "--from", help="Current level (default: junior)"),
    current_skills: Optional[str] = typer.Option(
        None, "--skills", "-s", help="JSON array of skill IDs you already have"
    ),
    fmt: OutputFormat = _FMT,
):
    """Generate a prioritized learning path for a target role."""
    loader = _loader()
    reg = _registry(loader)

    kwargs = {
        "target_function_id": function_id,
        "target_role_id": role_id,
        "target_level": level,
        "current_level": from_level,
    }
    if current_skills:
        try:
            kwargs["current_skills"] = json.loads(current_skills)
        except json.JSONDecodeError as e:
            formatters.print_error(f"Invalid JSON for --skills: {e}")
            raise typer.Exit(1)

    result = reg.call_skill("learning_path", **kwargs)
    if not result.ok:
        formatters.print_error(result.error)
        raise typer.Exit(1)
    _emit(result.data, fmt)
    formatters.print_learning_path(result.data)


@app.command(name="export")
def export_cmd(
    function_id: str = typer.Option(..., "--function", "-f", help="Function ID to export"),
    role_id: Optional[str] = typer.Option(None, "--role", "-r", help="Optional role ID (exports all roles if omitted)"),
    fmt: str = typer.Option("json", "--format", help="Output format: json or csv"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path (prints to stdout if omitted)"),
):
    """Export role data as CSV or JSON for spreadsheets and reports."""
    loader = _loader()

    if fmt == "csv":
        content = export_csv(loader, function_id, role_id)
    elif fmt == "json":
        content = export_json(loader, function_id, role_id)
    else:
        formatters.print_error(f"Unknown format: {fmt}. Use 'json' or 'csv'.")
        raise typer.Exit(1)

    if content.startswith("Error:"):
        formatters.print_error(content)
        raise typer.Exit(1)

    if output:
        Path(output).write_text(content, encoding="utf-8")
        formatters.console.print(f"Exported to [cyan]{output}[/cyan]")
    else:
        print(content)


@app.command()
def validate(
    path: str = typer.Option("taxonomy", "--path", "-p", help="Taxonomy directory to validate"),
):
    """Validate taxonomy YAML files against the schema."""
    try:
        from core.schema_validator import validate_taxonomy
    except ImportError:
        formatters.print_error(
            "jsonschema is required for validation. Install with: pip install skillich[dev]"
        )
        raise typer.Exit(1)

    report = validate_taxonomy(path)
    if report.ok:
        formatters.console.print(
            f"[bold green]All {report.files_checked} files passed validation.[/bold green]"
        )
    else:
        formatters.print_error(f"{len(report.errors)} validation error(s) found:")
        for err in report.errors:
            formatters.console.print(f"  [red]{err}[/red]")
        raise typer.Exit(1)


@app.command()
def transitions(
    function_id: str = typer.Option(..., "--function", "-f", help="Your current function ID"),
    role_id: str = typer.Option(..., "--role", "-r", help="Your current role ID"),
    limit: int = typer.Option(10, "--limit", "-n", help="Max results"),
    fmt: OutputFormat = _FMT,
):
    """Find roles you can transition to based on skill overlap."""
    loader = _loader()
    reg = _registry(loader)

    result = reg.call_skill(
        "career_advisor",
        action="find_transitions",
        source_function_id=function_id,
        source_role_id=role_id,
        limit=limit,
    )
    if not result.ok:
        formatters.print_error(result.error)
        raise typer.Exit(1)

    _emit(result.data, fmt)

    from rich.table import Table
    from rich.text import Text
    table = Table(title=f"Career Transitions from {result.data['source']}", show_lines=True)
    table.add_column("Role", style="bold")
    table.add_column("Function")
    table.add_column("Overlap", justify="right")
    table.add_column("Skills to Learn", justify="right")
    table.add_column("Gap Skills")
    for t in result.data["transitions"]:
        pct = t["skill_overlap_pct"]
        if pct >= 0.5:
            style = "green"
        elif pct >= 0.3:
            style = "yellow"
        else:
            style = "red"
        gaps = ", ".join(s["name"] for s in t["gap_skills"][:3])
        if len(t["gap_skills"]) > 3:
            gaps += f" (+{len(t['gap_skills']) - 3} more)"
        table.add_row(
            t["role"], t["function"],
            Text(f"{pct:.0%}", style=style),
            str(t["skills_to_learn"]),
            gaps,
        )
    formatters.console.print(table)


@app.command(name="content-check")
def content_check(
    path: str = typer.Option("taxonomy", "--path", "-p", help="Taxonomy directory"),
):
    """Check taxonomy content quality (thin descriptions, rating clusters, sources)."""
    from core.content_validator import validate_content

    report = validate_content(path)
    formatters.console.print(f"\n[bold]{report.summary()}[/bold]")
    formatters.console.print(
        f"  Roles: {report.stats.get('roles_checked', 0)}  "
        f"Skills: {report.stats.get('total_skills', 0)}  "
        f"Avg proficiency: {report.stats.get('avg_proficiency_chars', 0):.0f} chars  "
        f"Thin descriptions: {report.stats.get('thin_descriptions', 0)}\n"
    )

    if report.errors:
        formatters.console.print("[bold red]Errors:[/bold red]")
        for issue in report.errors:
            formatters.console.print(f"  [red]{issue}[/red]")

    if report.warnings:
        formatters.console.print(f"\n[bold yellow]Warnings ({len(report.warnings)}):[/bold yellow]")
        by_cat: dict[str, int] = {}
        for w in report.warnings:
            by_cat[w.category] = by_cat.get(w.category, 0) + 1
        for cat, count in sorted(by_cat.items(), key=lambda x: -x[1]):
            formatters.console.print(f"  {cat}: {count}")

    if not report.ok:
        raise typer.Exit(1)


@app.command()
def stats():
    """Show taxonomy statistics."""
    loader = _loader()
    formatters.print_stats(loader.stats)


@app.command()
def web(
    output: str = typer.Option("web/index.html", "--output", "-o", help="Output HTML file path"),
):
    """Generate the interactive web UI as a self-contained HTML file."""
    from web.generate import main as gen_main
    import sys
    sys.argv = ["generate", output]
    gen_main()


@app.command()
def serve():
    """Start the skillich MCP server (requires mcp extra)."""
    try:
        from mcp_server.server import main as mcp_main
    except ImportError:
        formatters.print_error("MCP server requires the mcp extra. Install with: pip install skillich[mcp]")
        raise typer.Exit(1)
    mcp_main()


@app.command()
def narrate(
    function_id: Optional[str] = typer.Option(None, "--function", "-f", help="Function ID"),
    role_id: Optional[str] = typer.Option(None, "--role", "-r", help="Role ID"),
    skill: Optional[str] = typer.Option(None, "--skill", "-s", help="Skill name for advice"),
    level: str = typer.Option("mid", "--level", "-l", help="Your current level (junior/mid/senior)"),
    brief: bool = typer.Option(False, "--brief", "-b", help="AI-resilience brief for a function"),
    fmt: OutputFormat = _FMT,
):
    """Generate plain-English career narratives using your local Ollama model.

    Requires Ollama running locally (default: http://localhost:11434).
    Set OLLAMA_ENDPOINT and OLLAMA_MODEL env vars to override.
    Returns raw taxonomy data if Ollama is unavailable.
    """
    from skills.taxonomy_skills.career_narrator import CareerNarratorSkill

    loader = _loader()
    narrator = CareerNarratorSkill(loader=loader)

    if skill:
        result = narrator.execute("skill_advice", skill_name=skill, current_level=level)
    elif brief and function_id:
        result = narrator.execute("resilience_brief", function_id=function_id)
    elif function_id and role_id:
        result = narrator.execute("role_summary", function_id=function_id, role_id=role_id)
    else:
        formatters.print_error(
            "Provide --function + --role for a role summary, "
            "--skill for skill advice, or --function + --brief for a resilience brief."
        )
        raise typer.Exit(1)

    _emit(result.data, fmt)

    if result.status.value == "partial":
        formatters.console.print(f"[yellow]⚠ {result.error}[/yellow]")

    if result.data:
        narrative = result.data.get("narrative") or result.data.get("advice")
        if narrative:
            from rich.panel import Panel
            model_label = result.data.get("model", "Ollama")
            formatters.console.print(Panel(
                narrative,
                title=f"[bold cyan]Career Insight[/bold cyan] · {model_label}",
                border_style="cyan",
            ))
        else:
            # Ollama unavailable — show raw data as a table
            from rich.table import Table
            table = Table(show_header=False, box=None)
            for k, v in result.data.items():
                table.add_row(f"[cyan]{k}[/cyan]", str(v))
            formatters.console.print(table)


@app.command()
def audit(
    stale_after: int = typer.Option(180, "--stale-after", help="Flag roles not reviewed in this many days"),
    fmt: OutputFormat = _FMT,
):
    """Find roles with stale AI impact data (not reviewed recently).

    Roles with a missing or unparseable last_reviewed date are always flagged.
    """
    from core.audit import find_stale_roles

    loader = _loader()
    stale = find_stale_roles(loader, days=stale_after)

    if fmt == OutputFormat.json:
        import dataclasses
        print(json.dumps([dataclasses.asdict(r) for r in stale], indent=2, default=str))
        raise typer.Exit(0)

    if fmt == OutputFormat.csv:
        import csv as csv_mod
        import dataclasses
        import io
        if stale:
            rows = [dataclasses.asdict(r) for r in stale]
            buf = io.StringIO()
            writer = csv_mod.DictWriter(buf, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
            print(buf.getvalue(), end="")
        raise typer.Exit(0)

    from rich.table import Table
    from rich.text import Text

    if not stale:
        formatters.console.print(
            f"[bold green]All roles reviewed within the last {stale_after} days. Taxonomy is fresh.[/bold green]"
        )
        return

    table = Table(title=f"Stale AI Impact Data (>{stale_after} days)", show_lines=True)
    table.add_column("Function", style="cyan", no_wrap=True)
    table.add_column("Role", style="bold")
    table.add_column("Last Reviewed")
    table.add_column("Days Ago", justify="right")
    table.add_column("AI Impact")
    table.add_column("Skills", justify="right")
    table.add_column("Confidence")

    for r in stale:
        days_str = str(r.days_since_review) if r.days_since_review is not None else "?"
        date_str = r.last_reviewed or "[red]missing[/red]"
        days_color = "red" if r.days_since_review is None or r.days_since_review > 365 else "yellow"
        table.add_row(
            r.function_name, r.role_name, date_str,
            Text(days_str, style=days_color),
            r.ai_impact_level, str(r.skill_count), r.confidence or "—",
        )

    formatters.console.print(table)
    formatters.console.print(
        f"\n[bold]{len(stale)} role(s) flagged.[/bold] "
        f"Update [cyan]last_reviewed[/cyan] in the role YAML when you refresh the data."
    )


if __name__ == "__main__":
    app()
