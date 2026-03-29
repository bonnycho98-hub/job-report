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
def get_site_stats(db: Session):
    return db.query(
        models.Site.id,
        models.Site.name,
        models.Site.url,
        models.Site.status,
        func.count(models.JobPosting.id).label("job_count")
    ).outerjoin(models.JobPosting, models.Site.id == models.JobPosting.site_id) \
     .group_by(models.Site.id).order_by(models.Site.id).all()
