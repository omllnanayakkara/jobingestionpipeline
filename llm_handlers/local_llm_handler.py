import os
import time
import httpx
import ollama
from llm_handlers.base import BaseLLM
import json
from models.job_listing import (
    JobCategory,
    JobType,
    ExperienceLevel,
    SalaryFrequency
)

MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5

class LocalLLMHandler(BaseLLM):

    def _enum_values(self,enum_cls) -> list[str]:
        return [member.value for member in enum_cls]


    def _build_template(self) -> dict:
        return {
            "category": self._enum_values(JobCategory),
            "job_type": self._enum_values(JobType),
            "experience_level": self._enum_values(ExperienceLevel),
            "location": "",
            "remote": False,
            "avg_salary": -1,
            "salary_frequency": self._enum_values(SalaryFrequency),
            "salary_currency": "",
            "min_experience_years": "",
            "required_skills": [""],
            "preferred_skills": [""],
            "education_requirements": [""],
        }


    def chat(self, input: dict):
        local_model = os.environ.get("NORMALIZER_MODEL", "").strip()
        if not local_model:
            return json.dumps(self._build_template())

        document = f"Title: {input["title"]}\n\nDescription:\n{input["description"]}"
        template = self._build_template()

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = ollama.chat(
                    model=local_model,
                    messages=[
                        {"role": "template", "content": json.dumps(template)},
                        {"role": "user", "content": document},
                    ],
                    think=False,
                    options={
                        "temperature": 0.2,
                        "top_k": 0.8
                    },
                    keep_alive=0
                )
                return response["message"]["content"]
            except (httpx.RemoteProtocolError, httpx.ConnectError, ollama.ResponseError, ConnectionError, OSError):
                if attempt == MAX_RETRIES:
                    return json.dumps(self._build_template())
                time.sleep(RETRY_BACKOFF_SECONDS * attempt) 

        return json.dumps(self._build_template())