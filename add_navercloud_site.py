from backend.database import SessionLocal
from backend import models

def add_navercloud():
    db = SessionLocal()
    try:
        url = "https://recruit.navercloudcorp.com/rcrt/list.do"
        existing = db.query(models.Site).filter(models.Site.url == url).first()
        if existing:
            print(f"Naver Cloud site already exists (ID: {existing.id})")
            return

        site = models.Site(
            name="네이버 클라우드 채용",
            url=url,
            status="active"
        )
        db.add(site)
        db.commit()
        db.refresh(site)
        print(f"Added Naver Cloud site (ID: {site.id})")
    finally:
        db.close()

if __name__ == "__main__":
    add_navercloud()
