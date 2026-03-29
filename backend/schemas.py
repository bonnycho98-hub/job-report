from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class SiteBase(BaseModel):
    name: str
    url: str
    selector_config: Optional[str] = None

class SiteCreate(SiteBase):
    pass

class Site(SiteBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class JobPostingBase(BaseModel):
    site_id: int
    title: str
    company: str
    position: str
    location: Optional[str] = None
    experience_level: Optional[str] = None
    employment_type: Optional[str] = None
    deadline: Optional[str] = None
    source_url: str
    description: Optional[str] = None
    posted_at: Optional[datetime] = None

class JobPostingCreate(JobPostingBase):
    pass

class JobPosting(JobPostingBase):
    id: int
    crawled_at: datetime

    class Config:
        from_attributes = True

class MatchResultBase(BaseModel):
    job_posting_id: int
    profile_id: int
    sub_group: Optional[str] = None
    match_score: float
    matched_keywords: Optional[str] = None
    week_number: int
    year: int

class MatchResultCreate(MatchResultBase):
    pass

class MatchResult(MatchResultBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
class SiteStats(BaseModel):
    id: int
    name: str
    url: str
    status: str
    job_count: int

    class Config:
        from_attributes = True
