from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import os
import re
import logging

from backend import models, schemas, crud
from backend.database import engine, get_db
from backend.crawler.engine import CrawlerEngine
from backend.matcher.engine import matcher_engine
from backend.exporter import export_to_html

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 테이블 자동 생성
    try:
        models.Base.metadata.create_all(bind=engine)
        logger.info("DB 테이블 초기화 완료")
    except Exception as e:
        logger.error(f"DB 초기화 실패: {e}")
        raise
    yield

app = FastAPI(title="Job Crawler Service", lifespan=lifespan)

# CORS 적용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 프론트엔드 정적 파일 서빙
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
os.makedirs(frontend_path, exist_ok=True)
app.mount("/static", StaticFiles(directory=frontend_path, html=True), name="static")

# 리포트 정적 파일 서빙 (export_to_html이 생성한 HTML)
reports_path = os.path.join(os.path.dirname(__file__), "..", "reports")
os.makedirs(reports_path, exist_ok=True)
app.mount("/reports", StaticFiles(directory=reports_path), name="reports")

@app.get("/")
def read_root():
    return RedirectResponse(url="/static/index.html")

@app.get("/mobile")
def read_mobile():
    return RedirectResponse(url="/static/mobile.html")

@app.get("/api/sites", response_model=List[schemas.Site])
def read_sites(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_sites(db, skip=skip, limit=limit)
@app.get("/api/stats/sites", response_model=List[schemas.SiteStats])
def get_site_statistics(db: Session = Depends(get_db)):
    return crud.get_site_stats(db)

@app.post("/api/sites", response_model=schemas.Site)
def create_site(site: schemas.SiteCreate, db: Session = Depends(get_db)):
    return crud.create_site(db, site)

@app.post("/api/crawl")
async def trigger_crawl(db: Session = Depends(get_db)):
    """크롤링 실행 및 데이터베이스 매칭 적용 엔드포인트"""
    crawler = CrawlerEngine(db)
    
    # v1 예시: DB에 등록된 사이트를 순회하며 임의의 샘플 파서 등록 (추후 동적 매핑 대체)
    # 실제로는 parser 모듈들을 여기서 register 해줍니다.
    # crawler.register_parser(site.id, WantedParser(site.id))
    
    results = await crawler.run()
    
    matched_results_summary = {"웅키": 0, "쵸키": 0}
    now = datetime.utcnow()
    week_num = now.isocalendar()[1]
    year = now.year
    
    # 해외 공고 블랙리스트
    FOREIGN_BLACKLIST = [
        # 일본
        "tokyo", "osaka", "japan", "日本", "東京", "大阪", "福岡",
        # 동남아
        "singapore", "vietnam", "hanoi", "ho chi minh",
        "bangkok", "thailand", "jakarta", "indonesia", "manila", "philippines",
        # 대만/중국
        "taipei", "taiwan", "台北", "台灣", "beijing", "shanghai", "shenzhen",
        # 미주/유럽
        "new york", "san francisco", "seattle", "los angeles", "austin",
        "london", "berlin", "amsterdam", "paris", "toronto", "vancouver",
    ]

    for job_data in results.get("raw_jobs", []):
        # 1. 중복 URL 방지
        source_url = job_data.get("source_url", "")
        existing_job = db.query(models.JobPosting).filter(models.JobPosting.source_url == source_url).first()
        if existing_job:
            continue

        # 2. 필터링: 인턴 및 해외 공고 제외 (DB 저장 전에 걸러냄)
        text_to_eval = f"{job_data.get('title', '')} {job_data.get('position', '')} {job_data.get('company', '')}".lower()
        if "인턴" in text_to_eval or re.search(r'\bintern\b', text_to_eval):
            continue
        if any(kw in text_to_eval for kw in FOREIGN_BLACKLIST):
            continue

        # 3. 필터 통과 → DB 저장
        db_job = models.JobPosting(
            site_id=job_data.get("site_id", 0),
            title=job_data.get("title", "Unknown"),
            company=job_data.get("company", "Unknown"),
            position=job_data.get("position", ""),
            source_url=source_url,
            deadline=job_data.get("deadline", "")
        )
        db.add(db_job)
        db.flush()

        # 3. 매칭 수행
        match_scores = matcher_engine.evaluate(text_to_eval)
        
        for match in match_scores:
            profile_id = 1 if match["profile_id"] == "웅키" else 2
            
            db_match = models.MatchResult(
                job_posting_id=db_job.id,
                profile_id=profile_id,
                sub_group=match["sub_group"],
                match_score=match["match_score"],
                matched_keywords=",".join(match["matched_keywords"]),
                week_number=week_num,
                year=year
            )
            db.add(db_match)
            if profile_id == 1:
                matched_results_summary["웅키"] += 1
            else:
                matched_results_summary["쵸키"] += 1
                
    db.commit()
    results["matched_summary"] = matched_results_summary
    return {"message": "success", "details": results}

@app.get("/api/results")
def get_results(profile: str = "웅키", week: int = None, year: int = None, db: Session = Depends(get_db)):
    query = db.query(models.MatchResult).join(models.JobPosting)
    if profile == "웅키":
        query = query.filter(models.MatchResult.profile_id == 1)
    else:
        query = query.filter(models.MatchResult.profile_id == 2)
        
    if week:
        query = query.filter(models.MatchResult.week_number == week)
    if year:
        query = query.filter(models.MatchResult.year == year)
        
    # 최신 등록순 정렬
    query = query.order_by(models.MatchResult.created_at.desc())
    results = query.all()
    
    formatted = []
    for r in results:
        formatted.append({
            "id": r.id,
            "company": r.job_posting.company,
            "title": r.job_posting.title,
            "position": r.job_posting.position,
            "url": r.job_posting.source_url,
            "deadline": r.job_posting.deadline,
            "score": r.match_score,
            "sub_group": r.sub_group,
            "matched_keywords": r.matched_keywords,
            "crawled_at": r.job_posting.crawled_at
        })
    return formatted

@app.post("/api/export")
def trigger_export(week: int = None, year: int = None, db: Session = Depends(get_db)):
    """현재 주차(혹은 입력 주차)에 대한 HTML 리포트 생성"""
    if not week or not year:
        now = datetime.utcnow()
        week = now.isocalendar()[1]
        year = now.year
        
    file_path = export_to_html(db, year, week)
    return {"message": "Export created successfully", "file_path": file_path}
