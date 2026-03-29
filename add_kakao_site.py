from backend.database import SessionLocal
from backend import models

def add_kakao():
    db = SessionLocal()
    try:
        kakao_url = "https://careers.kakao.com/jobs?skillSet=&page=1&company=KAKAO&part=TECHNOLOGY&employeeType=&keyword="
        # 이미 존재하는지 확인
        existing = db.query(models.Site).filter(models.Site.url == kakao_url).first()
        if existing:
            print(f"Kakao site already exists (ID: {existing.id})")
            return

        kakao_site = models.Site(
            name="카카오 채용",
            url=kakao_url,
            status="active"
        )
        db.add(kakao_site)
        db.commit()
        db.refresh(kakao_site)
        print(f"Added Kakao site (ID: {kakao_site.id})")
    finally:
        db.close()

if __name__ == "__main__":
    add_kakao()
