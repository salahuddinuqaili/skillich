"""Rich-formatted terminal output for the skillich CLI."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

IMPACT_COLORS = {
    "low": "green",
    "moderate": "yellow",
    "moderate-high": "dark_orange",
    "high": "red",
    "very-high": "bold red",
}


def _impact_color(level: str) -> str:
    return IMPACT_COLORS.get(level, "white")


def print_functions(functions: list[dict]) -> None:
    table = Table(title="skillich: Function Categories", show_lines=True)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("Roles", justify="right")
    table.add_column("Description")
    for f in functions:
        table.add_row(f["id"], f["name"], str(f["role_count"]), f["description"])
    console.print(table)


def print_roles(function_id: str, roles: list[dict]) -> None:
    table = Table(title=f"Roles in '{function_id}'", show_lines=True)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("Also Known As")
    table.add_column("Skills", justify="right")
    table.add_column("AI Impact")
    for r in roles:
        level = r.get("ai_impact_level", "")
        color = _impact_color(level)
        impact_text = Text(level, style=color)
        table.add_row(
            r["id"],
            r["name"],
            ", ".join(r.get("also_known_as", [])),
            str(r.get("skill_count", "")),
            impact_text,
        )
    console.print(table)


def print_role_detail(data: dict) -> None:
    # Header
    ai = data.get("ai_impact", {})
    level = ai.get("level", "")
    color = _impact_color(level)
    header = Text()
    header.append(data["name"], style="bold")
    header.append("  AI Impact: ")
    header.append(level, style=color)
    console.print(Panel(header, subtitle=", ".join(data.get("also_known_as", []))))

    console.print(f"\n{data.get('description', '')}\n")

    # AI Impact summary
    if ai.get("summary"):
        console.print(Panel(ai["summary"].strip(), title="AI Impact Summary", border_style=color))

    # AI breakdown columns
    if ai.get("automating") or ai.get("augmenting") or ai.get("preserving"):
        grid = Table(show_header=True, show_lines=True, title="AI Transformation Breakdown")
        grid.add_column("Automating (AI absorbs)", style="red")
        grid.add_column("Augmenting (AI + human)", style="yellow")
        grid.add_column("Preserving (stays human)", style="green")

        max_rows = max(
            len(ai.get("automating", [])),
            len(ai.get("augmenting", [])),
            len(ai.get("preserving", [])),
        )
        for i in range(max_rows):
            grid.add_row(
                ai["automating"][i] if i < len(ai.get("automating", [])) else "",
                ai["augmenting"][i] if i < len(ai.get("augmenting", [])) else "",
                ai["preserving"][i] if i < len(ai.get("preserving", [])) else "",
            )
        console.print(grid)

    # Levels
    levels = data.get("levels", [])
    if levels:
        lt = Table(title="Career Levels", show_lines=True)
        lt.add_column("Level", style="cyan")
        lt.add_column("Years")
        lt.add_column("Summary")
        for lvl in levels:
            lt.add_row(lvl["name"], lvl["years"], lvl["summary"])
        console.print(lt)

    # Skills
    skills = data.get("skills", [])
    if skills:
        st = Table(title=f"Skills ({len(skills)})", show_lines=True)
        st.add_column("Skill", style="bold")
        st.add_column("Category")
        st.add_column("AI Impact", justify="right")
        st.add_column("Description")
        for s in sorted(skills, key=lambda x: x.get("ai_impact_rating", 0)):
            rating = s.get("ai_impact_rating", 0)
            pct = f"{rating:.0%}"
            if rating <= 0.3:
                style = "green"
            elif rating <= 0.5:
                style = "yellow"
            else:
                style = "red"
            st.add_row(s["name"], s["category"], Text(pct, style=style), s["description"])
        console.print(st)


def print_search_results(query: str, results: list[dict], total: int) -> None:
    table = Table(title=f"Skill search: '{query}' ({total} results)", show_lines=True)
    table.add_column("Skill", style="bold")
    table.add_column("Category")
    table.add_column("AI Impact", justify="right")
    table.add_column("Description")
    for s in results:
        rating = s.get("ai_impact_rating", 0)
        pct = f"{rating:.0%}"
        if rating <= 0.3:
            style = "green"
        elif rating <= 0.5:
            style = "yellow"
        else:
            style = "red"
        table.add_row(s["name"], s["category"], Text(pct, style=style), s["description"])
    console.print(table)


def print_impact_comparison(data: dict) -> None:
    roles = data.get("roles", [])
    func = data.get("function", data.get("function_id", ""))
    table = Table(title=f"AI Impact Comparison: {func}", show_lines=True)
    table.add_column("Role", style="bold")
    table.add_column("AI Level")
    table.add_column("Avg Rating", justify="right")
    table.add_column("Bar")
    table.add_column("Most Resilient Skill")
    for r in sorted(roles, key=lambda x: x.get("avg_skill_automation", 0), reverse=True):
        level = r.get("ai_impact_level", "")
        color = _impact_color(level)
        avg = r.get("avg_skill_automation", 0)
        bar_len = int(avg * 30)
        bar = Text("+" * bar_len, style=color)
        resilient = r.get("most_resilient_skill", "")
        table.add_row(
            r.get("role", ""),
            Text(level, style=color),
            f"{avg:.0%}",
            bar,
            resilient if isinstance(resilient, str) else resilient.get("name", ""),
        )
    console.print(table)


def print_resilient_skills(skills: list[dict]) -> None:
    table = Table(title="Most AI-Resilient Skills (invest here)", show_lines=True)
    table.add_column("Skill", style="bold green")
    table.add_column("Role")
    table.add_column("Function")
    table.add_column("AI Impact", justify="right")
    for s in skills:
        table.add_row(
            s.get("skill", ""), s.get("role", ""), s.get("function", ""),
            f"{s.get('rating', 0):.0%}",
        )
    console.print(table)


def print_automatable_skills(skills: list[dict]) -> None:
    table = Table(title="Most Automatable Skills (AI is taking over)", show_lines=True)
    table.add_column("Skill", style="bold red")
    table.add_column("Role")
    table.add_column("Function")
    table.add_column("AI Impact", justify="right")
    for s in skills:
        table.add_row(
            s.get("skill", ""), s.get("role", ""), s.get("function", ""),
            f"{s.get('rating', 0):.0%}",
        )
    console.print(table)


def print_role_impact(data: dict) -> None:
    """Print role_impact output from ai_impact_analyzer."""
    level = data.get("level", "")
    color = _impact_color(level)
    header = Text()
    header.append(data.get("role", ""), style="bold")
    header.append("  AI Impact: ")
    header.append(level, style=color)
    console.print(Panel(header))

    if data.get("summary"):
        console.print(Panel(data["summary"].strip(), title="AI Impact Summary", border_style=color))

    # AI breakdown
    grid = Table(show_header=True, show_lines=True, title="AI Transformation Breakdown")
    grid.add_column("Automating (AI absorbs)", style="red")
    grid.add_column("Augmenting (AI + human)", style="yellow")
    grid.add_column("Preserving (stays human)", style="green")
    max_rows = max(
        len(data.get("automating", [])),
        len(data.get("augmenting", [])),
        len(data.get("preserving", [])),
    )
    for i in range(max_rows):
        grid.add_row(
            data["automating"][i] if i < len(data.get("automating", [])) else "",
            data["augmenting"][i] if i < len(data.get("augmenting", [])) else "",
            data["preserving"][i] if i < len(data.get("preserving", [])) else "",
        )
    console.print(grid)

    # Skills ranked by automation
    skills = data.get("skills", [])
    if skills:
        st = Table(title="Skills by AI Impact", show_lines=True)
        st.add_column("Skill", style="bold")
        st.add_column("AI Impact", justify="right")
        st.add_column("Detail")
        for s in skills:
            rating = s.get("rating", s.get("ai_impact_rating", 0))
            pct = f"{rating:.0%}"
            if rating <= 0.3:
                style = "green"
            elif rating <= 0.5:
                style = "yellow"
            else:
                style = "red"
            st.add_row(
                s.get("skill", s.get("name", "")),
                Text(pct, style=style),
                s.get("detail", ""),
            )
        console.print(st)


def print_assessment(data: dict) -> None:
    role_name = data.get("role", data.get("role_name", ""))
    console.print(
        Panel(
            f"[bold]{role_name}[/bold] at [cyan]{data['target_level']}[/cyan] level",
            title="Skill Assessment",
        )
    )

    summary = data.get("summary", {})
    if summary:
        console.print(
            f"  Gaps: [red]{summary.get('gaps', 0)}[/red]  "
            f"On track: [green]{summary.get('on_track', 0)}[/green]  "
            f"Strengths: [cyan]{summary.get('strengths', 0)}[/cyan]  "
            f"Unassessed: {summary.get('unassessed', 0)}/{summary.get('total_skills', 0)}\n"
        )

    if data.get("gaps"):
        gt = Table(title="Gaps (below target)", show_lines=True)
        gt.add_column("Skill", style="bold red")
        gt.add_column("Current")
        gt.add_column("Target")
        gt.add_column("AI Impact", justify="right")
        for g in data["gaps"]:
            gt.add_row(
                g.get("skill", g.get("skill_name", "")),
                g["current_level"],
                g["target_level"],
                f"{g.get('ai_impact_rating', 0):.0%}",
            )
        console.print(gt)

    if data.get("on_track"):
        ot = Table(title="On Track (at target)", show_lines=True)
        ot.add_column("Skill", style="bold green")
        ot.add_column("Level")
        for o in data["on_track"]:
            ot.add_row(o.get("skill", o.get("skill_name", "")), o["current_level"])
        console.print(ot)

    if data.get("strengths"):
        st = Table(title="Strengths (above target)", show_lines=True)
        st.add_column("Skill", style="bold cyan")
        st.add_column("Current")
        st.add_column("Target")
        for s in data["strengths"]:
            st.add_row(
                s.get("skill", s.get("skill_name", "")),
                s["current_level"],
                s["target_level"],
            )
        console.print(st)

    if data.get("unassessed"):
        ut = Table(title=f"Unassessed ({len(data['unassessed'])} skills)", show_lines=True)
        ut.add_column("Skill", style="dim")
        ut.add_column("Target Proficiency")
        for u in data["unassessed"]:
            ut.add_row(
                u.get("skill", u.get("skill_name", "")),
                u.get("target_description", "")[:100] + "...",
            )
        console.print(ut)


def print_learning_path(data: dict) -> None:
    role = data.get("role", data.get("target_role", ""))
    raw_transition = data.get("transition", f"{data.get('current_level', 'junior')} -> {data.get('target_level', '')}")
    transition = raw_transition.replace("\u2192", "->")
    console.print(
        Panel(
            f"[bold]{role}[/bold]: [yellow]{transition}[/yellow]",
            title="Learning Path",
        )
    )

    console.print(
        f"  Skills to develop: [bold]{data.get('total_skills_to_develop', '?')}[/bold]  "
        f"Already proficient: [green]{data.get('already_proficient', 0)}[/green]  "
        f"Levels to grow: [cyan]{data.get('levels_to_grow', '?')}[/cyan]\n"
    )

    phases = data.get("phases", [])
    for phase in phases:
        title = phase.get("focus", phase.get("name", f"Phase {phase.get('phase', '')}"))
        pt = Table(title=title, show_lines=True)
        pt.add_column("Skill", style="bold")
        pt.add_column("Category")
        pt.add_column("Priority", justify="right")
        pt.add_column("AI Impact", justify="right")
        for s in phase.get("skills", []):
            ai = s.get("ai_impact_rating", 0)
            if ai <= 0.3:
                style = "green"
            elif ai <= 0.5:
                style = "yellow"
            else:
                style = "red"
            pt.add_row(
                s.get("skill_name", s.get("name", "")),
                s.get("category", ""),
                f"{s.get('priority_score', 0):.2f}",
                Text(f"{ai:.0%}", style=style),
            )
        console.print(pt)


def print_stats(data: dict) -> None:
    console.print(
        Panel(
            f"[bold]{data['functions']}[/bold] functions, "
            f"[bold]{data['roles']}[/bold] roles, "
            f"[bold]{data['skills']}[/bold] skills",
            title="skillich Taxonomy",
        )
    )


def print_error(message: str) -> None:
    console.print(f"[bold red]Error:[/bold red] {message}")
