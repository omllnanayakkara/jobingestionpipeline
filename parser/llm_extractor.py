import json
import ollama
from models.job_listing import (
    JobCategory,
    JobType,
    ExperienceLevel,
    LLMExtractionInput,
    LLMExtractionOutput,
)

MODEL = "numind/nuextract3:q4_k_m"


def _enum_values(enum_cls) -> list[str]:
    return [member.value for member in enum_cls]


def _build_template() -> dict:
    return {
        "category": _enum_values(JobCategory),
        "job_type": _enum_values(JobType),
        "experience_level": _enum_values(ExperienceLevel),
        "location": "",
        "min_experience_years": "",
        "required_skills": [""],
        "preferred_skills": [""],
        "education_requirements": [""],
    }


def _enum_or_none(enum_cls, value):
    if not value:
        return None
    try:
        return enum_cls(value)
    except ValueError:
        return None


def extract(input_data: LLMExtractionInput) -> LLMExtractionOutput:
    document = f"Title: {input_data.title}\n\nDescription:\n{input_data.description}"
    template = _build_template()

    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "template", "content": json.dumps(template)},
            {"role": "user", "content": document},
        ],
        think=False,
        options={
            "temperature":0.2
        }
    )
    content = response["message"]["content"]
    data = json.loads(content)

    min_experience_years = data.get("min_experience_years")
    return LLMExtractionOutput(
        category=_enum_or_none(JobCategory, data.get("category")),
        job_type=_enum_or_none(JobType, data.get("job_type")),
        experience_level=_enum_or_none(ExperienceLevel, data.get("experience_level")),
        location=data.get("location") or None,
        min_experience_years=int(min_experience_years) if min_experience_years not in (None, "") else None,
        required_skills=[s for s in data.get("required_skills", []) if s],
        preferred_skills=[s for s in data.get("preferred_skills", []) if s],
        education_requirements=[s for s in data.get("education_requirements", []) if s],
    )
