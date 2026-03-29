#!/usr/bin/env python3
"""
카카오톡 "나에게 보내기" 알림 스크립트

GitHub Pages에 배포된 리포트 URL을 카카오톡으로 알림.
- 나에게 보내기: 본인 카톡에 리포트 카드가 도착
- 받은 메시지를 친구에게 수동 전달 가능

사용법:
    python scripts/notify_kakao.py
    python scripts/notify_kakao.py --week 13 --year 2026
"""

import os
import sys
import json
import argparse
from datetime import datetime

import requests

# 프로젝트 루트 기준
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


def load_env():
    """프로젝트 .env 파일 로드"""
    config = {}
    env_path = os.path.join(PROJECT_ROOT, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()
    return config


def get_report_summary(year, week):
    """deploy/reports/ 에서 리포트 HTML을 읽어 요약 정보 추출"""
    report_path = os.path.join(PROJECT_ROOT, "deploy", "reports", f"{year}-W{week}.html")
    
    if not os.path.exists(report_path):
        return None, None
    
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # OG description에서 요약 추출
    import re
    match = re.search(r'og:description"\s+content="([^"]+)"', content)
    description = match.group(1) if match else f"{year}년 {week}주차 채용공고 리포트"
    
    return report_path, description


def refresh_token_if_needed(config):
    """Access Token이 만료되었을 수 있으므로 Refresh Token으로 갱신 시도"""
    rest_api_key = config.get("KAKAO_REST_API_KEY", "")
    refresh_token = config.get("KAKAO_REFRESH_TOKEN", "")
    
    if not refresh_token:
        return config.get("KAKAO_ACCESS_TOKEN", "")
    
    url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": rest_api_key,
        "refresh_token": refresh_token,
    }
    
    response = requests.post(url, data=data)
    result = response.json()
    
    if "access_token" in result:
        # .env에 새 토큰 저장
        config["KAKAO_ACCESS_TOKEN"] = result["access_token"]
        if "refresh_token" in result:
            config["KAKAO_REFRESH_TOKEN"] = result["refresh_token"]
        
        env_path = os.path.join(PROJECT_ROOT, ".env")
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                lines = f.readlines()
        
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("KAKAO_ACCESS_TOKEN="):
                new_lines.append(f"KAKAO_ACCESS_TOKEN={result['access_token']}\n")
            elif stripped.startswith("KAKAO_REFRESH_TOKEN=") and "refresh_token" in result:
                new_lines.append(f"KAKAO_REFRESH_TOKEN={result['refresh_token']}\n")
            else:
                new_lines.append(line)
        
        with open(env_path, "w") as f:
            f.writelines(new_lines)
        
        return result["access_token"]
    
    return config.get("KAKAO_ACCESS_TOKEN", "")


def send_kakao_memo(access_token, report_url, summary, year, week):
    """카카오톡 '나에게 보내기' API로 리포트 알림 전송"""
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    template = {
        "object_type": "feed",
        "content": {
            "title": f"📋 {year}년 {week}주차 채용공고 리포트",
            "description": summary,
            "image_url": f"{report_url.rsplit('/', 1)[0]}/../og-image.png",
            "link": {
                "web_url": report_url,
                "mobile_web_url": report_url
            }
        },
        "buttons": [
            {
                "title": "리포트 보기",
                "link": {
                    "web_url": report_url,
                    "mobile_web_url": report_url
                }
            }
        ]
    }
    
    data = {"template_object": json.dumps(template, ensure_ascii=False)}
    response = requests.post(url, headers=headers, data=data)
    
    return response.status_code, response.json()


def main():
    parser = argparse.ArgumentParser(description="카카오톡으로 채용공고 리포트 알림 전송")
    parser.add_argument("--week", type=int, help="주차 번호")
    parser.add_argument("--year", type=int, help="연도")
    args = parser.parse_args()
    
    now = datetime.utcnow()
    year = args.year or now.year
    week = args.week or now.isocalendar()[1]
    
    config = load_env()
    
    # 설정값 확인
    username = config.get("GITHUB_USERNAME", "")
    repo = config.get("GITHUB_REPO_NAME", "job-report")
    
    if not username or username == "your_github_username":
        print("❌ .env 파일에 GITHUB_USERNAME을 설정해주세요!")
        sys.exit(1)
    
    access_token = config.get("KAKAO_ACCESS_TOKEN", "")
    if not access_token:
        print("❌ 카카오 Access Token이 없습니다. 먼저 인증을 실행하세요:")
        print("   python scripts/kakao_auth.py")
        sys.exit(1)
    
    # 토큰 갱신 시도
    access_token = refresh_token_if_needed(config)
    
    # 리포트 URL 생성
    report_url = f"https://{username}.github.io/{repo}/reports/{year}-W{week}.html"
    
    # 로컬 리포트에서 요약 추출
    _, summary = get_report_summary(year, week)
    if not summary:
        summary = f"{year}년 {week}주차 채용공고 매칭 리포트"
    
    print(f"\n📩 카카오톡 알림 전송 중...")
    print(f"   리포트: {report_url}")
    print(f"   요약:   {summary}")
    
    status_code, result = send_kakao_memo(access_token, report_url, summary, year, week)
    
    if status_code == 200:
        print(f"\n✅ 카카오톡 '나에게 보내기' 전송 완료!")
        print(f"   카카오톡을 확인해주세요.")
    elif status_code == 401:
        print(f"\n❌ 토큰이 만료되었습니다. 재인증하세요:")
        print(f"   python scripts/kakao_auth.py")
    else:
        print(f"\n❌ 전송 실패 (HTTP {status_code}): {result}")


if __name__ == "__main__":
    main()
