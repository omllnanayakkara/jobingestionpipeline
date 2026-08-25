from rapidfuzz import process, fuzz

strlist = [
    "software_engineering",
    "web_development",
    "mobile_development",
    "frontend_development",
    "backend_development",
    "full_stack_development",
    "data_science",
    "data_analytics",
    "data_engineering",
    "machine_learning",
    "ai_engineering",
    "devops",
    "cloud_engineering",
    "site_reliability",
    "cybersecurity",
    "networking",
    "systems_administration",
    "database",
    "qa_testing",
    "automation_testing",
    "ui_ux_design",
    "product_design",
    "it_support",
    "it_operations",
    "solutions_architecture",
    "software_architecture",
    "product_management",
    "project_management",
    "business_analysis",
    "technical_writing",
    "erp_crm",
    "embedded_systems",
    "iot",
    "blockchain_web3",
    "game_development",
    "it_management",
    "other_it",
]

def find_best_match(
    value: str,
    choices: list[str],
    threshold: float = 70,
):
    result = process.extractOne(
        value,
        choices,
        scorer=fuzz.WRatio,
    )

    if result is None:
        return "Other"

    match, score, _ = result

    if score < threshold:
        return "Other"

    return match

print(find_best_match("cloud architect", strlist))