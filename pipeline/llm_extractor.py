import json
from llm_handlers.local_llm_handler import LocalLLMHandler
from utils.enums import enum_or_none
from models.job_listing import (
    JobCategory,
    JobType,
    ExperienceLevel,
    LLMExtractionInput,
    LLMExtractionOutput,
    SalaryFrequency
)



def extract(input_data: LLMExtractionInput) -> LLMExtractionOutput:
    handler = LocalLLMHandler()
    content = handler.chat({
        "title": input_data.title,
        "description": input_data.description,
    })
    data = json.loads(content)

    min_experience_years = data.get("min_experience_years")
    return LLMExtractionOutput(
        category=enum_or_none(JobCategory, data.get("category")),
        job_type=enum_or_none(JobType, data.get("job_type")),
        experience_level=enum_or_none(ExperienceLevel, data.get("experience_level")),
        location=data.get("location") or None,
        remote=data.get("remote") or None,
        avg_salary=data.get("avg_salary") if data.get("avg_salary") and data.get("avg_salary") > 0 else None,
        salary_frequency=enum_or_none(SalaryFrequency, data.get("salary_frequency")),
        salary_currency=data.get("salary_currency") or None,
        min_experience_years=int(min_experience_years) if min_experience_years not in (None, "") else None,
        required_skills=[s for s in data.get("required_skills", []) if s],
        preferred_skills=[s for s in data.get("preferred_skills", []) if s],
        education_requirements=[s for s in data.get("education_requirements", []) if s],
    )
