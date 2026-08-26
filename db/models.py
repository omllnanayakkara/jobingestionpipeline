import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Float, Boolean, Integer, DateTime, Text, Index, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from pgvector.sqlalchemy import Vector

from models.job_listing import JobCategory, JobType, ExperienceLevel, SalaryFrequency


def _enum_column(enum_cls):
    return SAEnum(enum_cls, values_callable=lambda e: [m.value for m in e])


class Base(DeclarativeBase):
    pass


class Run(Base):
    __tablename__ = "Run"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    duration: Mapped[int | None] = mapped_column(Integer)
    record_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    record_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    job_listings: Mapped[list["JobListing"]] = relationship(back_populates="run")


class Company(Base):
    __tablename__ = "Company"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True)
    size: Mapped[int | None] = mapped_column(Integer)
    location: Mapped[str | None] = mapped_column(String)
    glassdoor_rating: Mapped[float | None] = mapped_column(Float)
    glassdoor_summary: Mapped[str | None] = mapped_column(String)
    company_url: Mapped[str | None] = mapped_column(String)
    company_logo_url: Mapped[str | None] = mapped_column(String)
    company_linkedin_url: Mapped[str | None] = mapped_column(String)

    record_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    record_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    job_listings: Mapped[list["JobListing"]] = relationship(back_populates="company")


class JobListing(Base):
    __tablename__ = "JobListing"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[str] = mapped_column(String, unique=True)
    source: Mapped[str] = mapped_column(String)
    source_url: Mapped[str] = mapped_column(String)
    raw: Mapped[str | None] = mapped_column(Text)

    title: Mapped[str] = mapped_column(String)
    summary: Mapped[str | None] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)

    job_type: Mapped[JobType | None] = mapped_column(_enum_column(JobType))
    category: Mapped[JobCategory | None] = mapped_column(_enum_column(JobCategory))
    location: Mapped[str | None] = mapped_column(String)
    remote: Mapped[bool | None] = mapped_column(Boolean)

    min_salary: Mapped[float | None] = mapped_column(Float)
    max_salary: Mapped[float | None] = mapped_column(Float)
    avg_salary: Mapped[float | None] = mapped_column(Float)
    salary_currency: Mapped[str | None] = mapped_column(String)
    salary_frequency: Mapped[SalaryFrequency | None] = mapped_column(_enum_column(SalaryFrequency))

    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    required_skills: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    preferred_skills: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    experience_level: Mapped[ExperienceLevel | None] = mapped_column(_enum_column(ExperienceLevel))
    min_experience_years: Mapped[int | None] = mapped_column(Integer)
    education_requirements: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    # 384-d embeddings
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(384),
        nullable=True
    )

    canonical_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    record_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    record_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("Company.id"))
    company: Mapped["Company"] = relationship(back_populates="job_listings")

    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("Run.id"))
    run: Mapped["Run"] = relationship(back_populates="job_listings")

    __table_args__ = (
        Index("ix_joblisting_source", "source"),
        Index("ix_joblisting_category", "category"),
        Index("ix_joblisting_job_type", "job_type"),
        Index("ix_joblisting_posted_at", "posted_at"),
        Index("idx_source_ext_id", "source", "external_id"),
        UniqueConstraint("source", "external_id", name="uq_joblisting_source_external_id")
    )
