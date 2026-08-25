from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from rapidfuzz import process, fuzz, utils as fuzz_utils


class JobCategory(Enum):
    SOFTWARE_ENGINEERING = "software_engineering"
    WEB_DEVELOPMENT = "web_development"
    MOBILE_DEVELOPMENT = "mobile_development"
    FRONTEND_DEVELOPMENT = "frontend_development"
    BACKEND_DEVELOPMENT = "backend_development"
    FULL_STACK_DEVELOPMENT = "full_stack_development"

    DATA_SCIENCE = "data_science"
    DATA_ANALYTICS = "data_analytics"
    DATA_ENGINEERING = "data_engineering"
    MACHINE_LEARNING = "machine_learning"
    AI_ENGINEERING = "ai_engineering"

    DEVOPS = "devops"
    CLOUD_ENGINEERING = "cloud_engineering"
    SITE_RELIABILITY = "site_reliability"

    CYBERSECURITY = "cybersecurity"
    NETWORKING = "networking"
    SYSTEMS_ADMINISTRATION = "systems_administration"

    DATABASE = "database"
    QA_TESTING = "qa_testing"
    AUTOMATION_TESTING = "automation_testing"

    UI_UX_DESIGN = "ui_ux_design"
    PRODUCT_DESIGN = "product_design"

    IT_SUPPORT = "it_support"
    IT_OPERATIONS = "it_operations"

    SOLUTIONS_ARCHITECTURE = "solutions_architecture"
    SOFTWARE_ARCHITECTURE = "software_architecture"

    PRODUCT_MANAGEMENT = "product_management"
    PROJECT_MANAGEMENT = "project_management"

    BUSINESS_ANALYSIS = "business_analysis"
    TECHNICAL_WRITING = "technical_writing"

    ERP_CRM = "erp_crm"
    EMBEDDED_SYSTEMS = "embedded_systems"
    IOT = "iot"

    BLOCKCHAIN_WEB3 = "blockchain_web3"
    GAME_DEVELOPMENT = "game_development"

    IT_MANAGEMENT = "it_management"
    OTHER = "other"             # Unspecified


class JobType(Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    OTHER = "other"             # Unspecified


class ExperienceLevel(Enum):
    """
    0 years => intern,
    0–1 years => entry,
    1–3 years => junior,
    2–5 years => mid,
    5–8+ years => senior,
    7–12+ years => lead,
    10–15+ years => staff,
    12–18+ years => principal,
    10–15+ years => architect,
    7–12+ years => manager,
    10–15+ years => director,
    12–20+ years => executive,
    Unspecified => other
    """
    INTERN = "intern"          # 0 years
    ENTRY = "entry"            # 0–1 years
    JUNIOR = "junior"          # 1–3 years
    MID = "mid"                # 2–5 years
    SENIOR = "senior"          # 5–8+ years
    LEAD = "lead"              # 7–12+ years
    STAFF = "staff"            # 10–15+ years
    PRINCIPAL = "principal"    # 12–18+ years
    ARCHITECT = "architect"    # 10–15+ years
    MANAGER = "manager"        # 7–12+ years
    DIRECTOR = "director"      # 10–15+ years
    EXECUTIVE = "executive"    # 12–20+ years
    OTHER = "other"            # Unspecified


CATEGORY_MATCH_THRESHOLD = 70  # 0-100; tune once real data is eyeballed


def match_job_category(raw_category: Optional[str], threshold: float = CATEGORY_MATCH_THRESHOLD) -> Optional[JobCategory]:
    if not raw_category:
        return None
    labels = {member: member.name.replace("_", " ").title() for member in JobCategory if member is not JobCategory.OTHER}
    result = process.extractOne(
        raw_category, labels.values(), scorer=fuzz.WRatio, processor=fuzz_utils.default_process
    )
    if result is None:
        return None
    matched_label, score, _ = result
    if score < threshold:
        return None
    return next(member for member, label in labels.items() if label == matched_label)


@dataclass
class NormalizedListing:
    # Identity & provenance
    external_id: str
    source: str
    source_url: str
    raw: str

    # Content
    title: str
    summary: Optional[str]
    description: str

    # Company
    company_name: Optional[str]
    company_url: Optional[str]
    company_logo_url: Optional[str]

    # Employment
    job_type: Optional[JobType]
    category: Optional[JobCategory]
    location: Optional[str]
    remote: Optional[bool]

    # Compensation
    min_salary: Optional[float]
    max_salary: Optional[float]
    avg_salary: Optional[float]
    salary_currency: Optional[str]
    salary_frequency: Optional[str]

    # Lifecycle
    posted_at: Optional[datetime]
    updated_at: Optional[datetime]
    expires_at: Optional[datetime]

    # Metrics
    # views_count: Optional[int]


@dataclass
class JobListing(NormalizedListing):
    # Enriched fields: not populated by scrapers or normalization. Filled in
    # later by a separate parsing/NLP stage (the `parser/` package) that
    # reads `description` and extracts structured signal from free text.
    required_skills: list[str]
    preferred_skills: list[str]
    experience_level: Optional[ExperienceLevel]
    min_experience_years: Optional[int]
    education_requirements: Optional[list[str]]

@dataclass
class KnownFields:
    """
    Known values to populate missing/noisy values.
    """
    category: JobCategory | None = None
    experience_level: ExperienceLevel | None = None
    job_type: JobType | None = None

@dataclass 
class FreeTextFields:
    """
    LLM can decide sutable values based on the content given.
    """
    location: str | None = None
    min_experience_years: int | None = None
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    education_requirements: list[str] = field(default_factory=list)

@dataclass
class LLMExtractionInput:
    title: str
    description: str
    known_fields: KnownFields
    free_text_fields: FreeTextFields

@dataclass
class LLMExtractionOutput:
    category: JobCategory | None = None
    experience_level: ExperienceLevel | None = None
    job_type: JobType | None = None
    location: str | None = None
    min_experience_years: int | None = None
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    education_requirements: list[str] = field(default_factory=list)