"""skillich demo: explore AI impact across tech roles."""


from core.registry import SkillRegistry
from core.taxonomy import TaxonomyLoader
from skills.taxonomy_skills.role_explorer import RoleExplorerSkill
from skills.taxonomy_skills.ai_impact_analyzer import AIImpactAnalyzerSkill


def main():
    print("=== skillich: The AI Skills Transformation Guide ===\n")

    # Load taxonomy
    loader = TaxonomyLoader("taxonomy")
    stats = loader.stats
    print(f"Loaded: {stats['functions']} functions, {stats['roles']} roles, {stats['skills']} skills\n")

    # Show all functions
    for func in loader.list_functions():
        roles = ", ".join(r.name for r in func.roles)
        print(f"  {func.name}: {roles}")

    # AI Impact demo
    print("\n--- AI Impact: Engineering Roles (ranked by automation exposure) ---\n")
    registry = SkillRegistry()
    registry.register(AIImpactAnalyzerSkill())

    result = registry.call_skill("ai_impact_analyzer", action="compare_roles", function_id="engineering")
    for role in result.data["roles"]:
        bar = "#" * int(role["avg_skill_automation"] * 20)
        print(f"  {role['role']:.<40} {role['avg_skill_automation']:.0%} {bar}")
        print(f"    Most resilient skill: {role['most_resilient_skill']}")

    # Top 5 most AI-resilient skills across ALL roles
    print("\n--- Top 10 Most AI-Resilient Skills (invest here) ---\n")
    result = registry.call_skill("ai_impact_analyzer", action="most_resilient", limit=10)
    for s in result.data["skills"]:
        print(f"  {s['rating']:.0%} automatable | {s['skill']} ({s['role']})")

    # Export for LLMs
    print("\n--- LLM Integration ---")
    registry.register(RoleExplorerSkill())
    print(f"  OpenAI tools:    {len(registry.to_openai_tools())}")
    print(f"  Anthropic tools: {len(registry.to_anthropic_tools())}")
    print(f"  MCP tools:       {len(registry.to_mcp_tools())}")


if __name__ == "__main__":
    main()
