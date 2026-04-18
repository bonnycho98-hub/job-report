#!/usr/bin/env python3
"""GitHub Actions 자동 크롤링용 독립 실행 스크립트"""
import asyncio
import sys
import os
import re
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, get_db
from backend import models
from backend.crawler.engine import CrawlerEngine
from backend.matcher.engine import matcher_engine

FOREIGN_BLACKLIST = [
    "tokyo", "osaka", "japan", "日本", "東京", "大阪", "福岡",
    "singapore", "vietnam", "hanoi", "ho chi minh",
    "bangkok", "thailand", "jakarta", "indonesia", "manila", "philippines",
    "taipei", "taiwan", "台北", "台灣", "beijing", "shanghai", "shenzhen",
    "new york", "san francisco", "seattle", "los angeles", "austin",
    "london", "berlin", "amsterdam", "paris", "toronto", "vancouver",
]


async def main():
    models.Base.metadata.create_all(bind=engine)
    db = next(get_db())

    try:
        crawler = CrawlerEngine(db)
        results = await crawler.run()

        matched_summary = {"웅키": 0, "쵸키": 0}
        now = datetime.utcnow()
        week_num = now.isocalendar()[1]
        year = now.year

        for job_data in results.get("raw_jobs", []):
            source_url = job_data.get("source_url", "")
            if db.query(models.JobPosting).filter(models.JobPosting.source_url == source_url).first():
                continue

            text = f"{job_data.get('title', '')} {job_data.get('position', '')} {job_data.get('company', '')}".lower()
            if "인턴" in text or re.search(r'\bintern\b', text):
                continue
            if any(kw in text for kw in FOREIGN_BLACKLIST):
                continue

            db_job = models.JobPosting(
                site_id=job_data.get("site_id", 0),
                title=job_data.get("title", "Unknown"),
                company=job_data.get("company", "Unknown"),
                position=job_data.get("position", ""),
                source_url=source_url,
                deadline=job_data.get("deadline", ""),
            )
            db.add(db_job)
            db.flush()

            for match in matcher_engine.evaluate(text):
                profile_id = 1 if match["profile_id"] == "웅키" else 2
                db.add(models.MatchResult(
                    job_posting_id=db_job.id,
                    profile_id=profile_id,
                    sub_group=match["sub_group"],
                    match_score=match["match_score"],
                    matched_keywords=",".join(match["matched_keywords"]),
                    week_number=week_num,
                    year=year,
                ))
                if profile_id == 1:
                    matched_summary["웅키"] += 1
                else:
                    matched_summary["쵸키"] += 1

        db.commit()

        print(json.dumps({
            "success": results.get("success", 0),
            "failed": results.get("failed", 0),
            "raw_jobs": len(results.get("raw_jobs", [])),
            "matched_summary": matched_summary,
        }))

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
