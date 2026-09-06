LINKEDIN_DETAIL_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "company_name": {"type": "string"},
        "company_url": {"type": "string"},
        "company_logo_url": {"type": "string"},
        "location": {"type": "string"},
        "description": {"type": "string"},
        "job_type": {"type": "string"},
        "remote": {"type": "boolean"},
        "posted_at": {"type": "string"},
        "updated_at": {"type": "string"},
        "expires_at": {"type": "string"},
        "salary_text": {"type": "string"}
    },
    "required": ["title", "company_name", "description"]
}

LINKEDIN_DISCOVERY_SCHEMA = {
    "type": "object",
    "properties": {
        "jobs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "company_name": {"type": "string"},
                    "location": {"type": "string"},
                    "job_url": {"type": "string"},
                    "job_id": {"type": "string"}
                },
                "required": ["title", "job_url"]
            }
        }
    },
    "required": ["jobs"]
}