from sqlalchemy.orm import Session
from sqlalchemy import func

from . import models, schemas
from datetime import datetime

def get_site(db: Session, site_id: int):
    return db.query(models.Site).filter(models.Site.id == site_id).first()

def get_sites(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Site).offset(skip).limit(limit).all()

def create_site(db: Session, site: schemas.SiteCreate):
    db_site = models.Site(name=site.name, url=site.url, selector_config=site.selector_config)
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    return db_site

def update_site_status(db: Session, site_id: int, status: str):
    db_site = db.query(models.Site).filter(models.Site.id == site_id).first()
    if db_site:
        db_site.status = status
        db.commit()
        db.refresh(db_site)
    return db_site
def delete_site(db: Session, site_id: int):
    db_site = db.query(models.Site).filter(models.Site.id == site_id).first()
    if not db_site:
        return False
    # 연결된 job_postings 및 match_results 먼저 삭제
    job_ids = [j.id for j in db.query(models.JobPosting.id).filter(models.JobPosting.site_id == site_id).all()]
    if job_ids:
        db.query(models.MatchResult).filter(models.MatchResult.job_posting_id.in_(job_ids)).delete(synchronize_session=False)
        db.query(models.JobPosting).filter(models.JobPosting.site_id == site_id).delete(synchronize_session=False)
    db.delete(db_site)
    db.commit()
    return True

def get_site_stats(db: Session):
    return db.query(
        models.Site.id,
        models.Site.name,
        models.Site.url,
        models.Site.status,
        func.count(models.JobPosting.id).label("job_count")
    ).outerjoin(models.JobPosting, models.Site.id == models.JobPosting.site_id) \
     .group_by(models.Site.id).order_by(models.Site.id).all()
