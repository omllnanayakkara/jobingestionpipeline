import os
from urllib.parse import urlsplit, urlunsplit

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()


def _database_url() -> str:
    raw_url = os.environ["DATABASE_URL"]
    parts = urlsplit(raw_url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


engine = create_engine(_database_url())
SessionLocal = sessionmaker(bind=engine)