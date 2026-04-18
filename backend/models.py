from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Site(Base):
    __tablename__ = "sites"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    url = Column(String, unique=True, index=True)
    status = Column(String, default="active")  # active, parse_error, timeout
    selector_config = Column(Text, nullable=True)  # JSON string for parse config
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    job_postings = relationship("JobPosting", back_populates="site")


class JobPosting(Base):
    __tablename__ = "job_postings"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"))
    title = Column(String, index=True)
    company = Column(String, index=True)
    position = Column(String)
    location = Column(String, nullable=True)
    experience_level = Column(String, nullable=True)
    employment_type = Column(String, nullable=True)
    deadline = Column(String, nullable=True)
    source_url = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    posted_at = Column(DateTime, nullable=True)
    crawled_at = Column(DateTime, default=datetime.utcnow)

    site = relationship("Site", back_populates="job_postings")
    match_results = relationship("MatchResult", back_populates="job_posting")


class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    keywords = Column(Text)  # JSON string
    sub_groups = Column(Text, nullable=True)  # JSON string, for profile B (B-1, B-2...)


class MatchResult(Base):
    __tablename__ = "match_results"

    id = Column(Integer, primary_key=True, index=True)
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"))
    profile_id = Column(Integer, ForeignKey("profiles.id"))
    sub_group = Column(String, nullable=True)
    match_score = Column(Float, default=0.0)
    matched_keywords = Column(Text, nullable=True)  # JSON string of matched keywords
    week_number = Column(Integer, index=True)
    year = Column(Integer, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    job_posting = relationship("JobPosting", back_populates="match_results")
    profile = relationship("Profile")


class CrawlSession(Base):
    __tablename__ = "crawl_sessions"

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    total_sites = Column(Integer, default=0)
    success = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    new_jobs = Column(Integer, default=0)
    matched_a = Column(Integer, default=0)
    matched_b = Column(Integer, default=0)
    site_results = Column(Text, nullable=True)  # JSON: [{name, status, jobs_found, error}]
