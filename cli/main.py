"""skillich CLI -- explore AI impact on tech roles from the terminal."""

import json
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


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def explore(
    function_id: Optional[str] = typer.Option(None, "--function", "-f", help="Function ID, e.g. 'engineering'"),
    role_id: Optional[str] = typer.Option(None, "--role", "-r", help="Role ID, e.g. 'backend'"),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search skills by keyword"),
):
    """Browse functions, roles, and skills in the taxonomy."""
    loader = _loader()
    reg = _registry(loader)

    if search:
        result = reg.call_skill("role_explorer", action="search_skills", query=search)
        if not result.ok:
            formatters.print_error(result.error)
            raise typer.Exit(1)
        formatters.print_search_results(search, result.data["skills"], result.data["count"])
    elif function_id and role_id:
        result = reg.call_skill("role_explorer", action="get_role", function_id=function_id, role_id=role_id)
        if not result.ok:
            formatters.print_error(result.error)
            raise typer.Exit(1)
        formatters.print_role_detail(result.data)
    elif function_id:
        result = reg.call_skill("role_explorer", action="list_roles", function_id=function_id)
        if not result.ok:
            formatters.print_error(result.error)
            raise typer.Exit(1)
        formatters.print_roles(function_id, result.data["roles"])
    else:
        result = reg.call_skill("role_explorer", action="list_functions")
        if not result.ok:
            formatters.print_error(result.error)
            raise typer.Exit(1)
        formatters.print_functions(result.data["functions"])


@app.command()
def impact(
    function_id: Optional[str] = typer.Option(None, "--function", "-f", help="Function ID"),
    role_id: Optional[str] = typer.Option(None, "--role", "-r", help="Role ID"),
    compare: bool = typer.Option(False, "--compare", "-c", help="Compare all roles in a function"),
    resilient: bool = typer.Option(False, "--resilient", help="Show most AI-resilient skills"),
    automatable: bool = typer.Option(False, "--automatable", help="Show most automatable skills"),
    limit: int = typer.Option(20, "--limit", "-n", help="Max results"),
):
    """Analyze AI impact on tech roles and skills."""
    loader = _loader()
    reg = _registry(loader)

    if resilient:
        result = reg.call_skill("ai_impact_analyzer", action="most_resilient", limit=limit)
        if not result.ok:
            formatters.print_error(result.error)
            raise typer.Exit(1)
        formatters.print_resilient_skills(result.data["skills"])
    elif automatable:
        result = reg.call_skill("ai_impact_analyzer", action="most_automatable", limit=limit)
        if not result.ok:
            formatters.print_error(result.error)
            raise typer.Exit(1)
        formatters.print_automatable_skills(result.data["skills"])
    elif compare and function_id:
        result = reg.call_skill("ai_impact_analyzer", action="compare_roles", function_id=function_id)
        if not result.ok:
            formatters.print_error(result.error)
            raise typer.Exit(1)
        formatters.print_impact_comparison(result.data)
    elif function_id and role_id:
        result = reg.call_skill(
            "ai_impact_analyzer", action="role_impact", function_id=function_id, role_id=role_id
        )
        if not result.ok:
            formatters.print_error(result.error)
            raise typer.Exit(1)
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
        # Group by category
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


if __name__ == "__main__":
    app()
