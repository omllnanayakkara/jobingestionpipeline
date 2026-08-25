from uuid import UUID
from db.models import Run
from sqlalchemy import insert, update
from datetime import datetime, timezone
from db.session import SessionLocal

def start_run():
    data = {
        "record_created_at":datetime.now(timezone.utc)
    }

    with SessionLocal.begin() as session:
        stmt = insert(Run).values(
            data
        ).returning(Run.id)
        return session.execute(stmt).scalar_one()

def update_run(run_id:UUID, data:dict):

    with SessionLocal.begin() as session:
        stmt = update(Run).where(
            Run.id == run_id
        ).values(
            data
        ).returning(Run.id)
        return session.execute(stmt).scalar_one()

