#!/usr/bin/env python3
"""
텔레그램 봇을 통한 채용공고 리포트 알림 스크립트

GitHub Pages에 배포된 리포트 URL을 텔레그램으로 전송합니다.

사전 준비:
    1. 텔레그램에서 @BotFather 에게 메시지 → /newbot → 봇 생성
    2. 받은 토큰을 .env 파일의 TELEGRAM_BOT_TOKEN 에 입력
    3. 봇에게 아무 메시지를 보낸 후, 이 스크립트 실행 시 chat_id 자동 탐색
    4. 또는 직접 TELEGRAM_CHAT_ID 를 .env에 입력

사용법:
    python scripts/notify_telegram.py
    python scripts/notify_telegram.py --week 13 --year 2026
    python scripts/notify_telegram.py --setup   # chat_id 자동 탐색
"""

import os
import sys
import json
import argparse
import re
from datetime import datetime

import requests

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")


def load_env():
    config = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()
    return config


def save_to_env(key, value):
    """특정 키를 .env 파일에 저장 (기존 키면 업데이트, 없으면 추가)"""
    lines = []
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r") as f:
            lines = f.readlines()
    
    found = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            found = True
        else:
            new_lines.append(line)
    
    if not found:
        new_lines.append(f"{key}={value}\n")
    
    with open(ENV_PATH, "w") as f:
        f.writelines(new_lines)


def get_report_summary(year, week):
    """reports/ 에서 리포트 HTML을 읽어 요약 추출"""
    report_path = os.path.join(PROJECT_ROOT, "reports", f"{year}-W{week}.html")
    
    if not os.path.exists(report_path):
        return None
    
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    match = re.search(r'og:description"\s+content="([^"]+)"', content)
    return match.group(1) if match else f"{year}년 {week}주차 채용공고 리포트"


def setup_chat_id(bot_token):
    """봇에게 온 메시지에서 chat_id를 자동 탐색"""
    print("\n🔍 봇에게 온 메시지에서 Chat ID를 찾는 중...")
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    
    response = requests.get(url)
    data = response.json()
    
    if not data.get("ok") or not data.get("result"):
        print("\n❌ 봇에게 온 메시지가 없습니다.")
        print("   텔레그램에서 봇에게 아무 메시지(예: /start)를 보낸 후 다시 실행하세요.")
        return None
    
    # 가장 최근 메시지의 chat_id
    chats = {}
    for update in data["result"]:
        msg = update.get("message", {})
        chat = msg.get("chat", {})
        chat_id = chat.get("id")
        chat_name = chat.get("first_name", "") or chat.get("title", "")
        chat_type = chat.get("type", "")
        if chat_id:
            chats[chat_id] = {"name": chat_name, "type": chat_type}
    
    if not chats:
        print("\n❌ Chat ID를 찾을 수 없습니다.")
        return None
    
    print(f"\n📋 발견된 채팅 목록:")
    for cid, info in chats.items():
        print(f"   [{info['type']}] {info['name']} → Chat ID: {cid}")
    
    # 첫 번째 (가장 오래된) 개인 채팅 선택
    selected = list(chats.keys())[0]
    print(f"\n✅ Chat ID 선택: {selected}")
    
    save_to_env("TELEGRAM_CHAT_ID", str(selected))
    print(f"   .env 파일에 TELEGRAM_CHAT_ID={selected} 저장 완료!")
    
    return selected


def send_telegram_message(bot_token, chat_id, report_url, summary, year, week):
    """텔레그램으로 리포트 알림 메시지 전송"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # HTML 포맷 메시지 (텔레그램은 HTML 마크업 지원)
    text = (
        f"📋 <b>{year}년 {week}주차 채용공고 매칭 리포트</b>\n"
        f"\n"
        f"{summary}\n"
        f"\n"
        f"🔗 <a href=\"{report_url}\">리포트 보기</a>"
    )
    
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,  # URL 프리뷰 표시
    }
    
    response = requests.post(url, json=payload)
    return response.status_code, response.json()


def send_telegram_message_with_buttons(bot_token, chat_id, report_url, summary, year, week):
    """인라인 버튼이 포함된 리포트 알림 메시지 전송"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    text = (
        f"📋 <b>{year}년 {week}주차 채용공고 매칭 리포트</b>\n"
        f"\n"
        f"{summary}\n"
        f"\n"
        f"아래 버튼을 눌러 리포트를 확인하세요!"
    )
    
    # 인라인 키보드 버튼
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "📊 리포트 보기", "url": report_url}
            ],
            [
                {"text": "📱 프로필 A (마케팅)", "url": report_url + "?tab=A"},
                {"text": "💼 프로필 B (기획)", "url": report_url + "?tab=B"}
            ]
        ]
    }
    
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": json.dumps(keyboard),
        "disable_web_page_preview": False,
    }
    
    response = requests.post(url, json=payload)
    return response.status_code, response.json()


def main():
    parser = argparse.ArgumentParser(description="텔레그램으로 채용공고 리포트 알림 전송")
    parser.add_argument("--week", type=int, help="주차 번호")
    parser.add_argument("--year", type=int, help="연도")
    parser.add_argument("--setup", action="store_true", help="Chat ID 자동 탐색")
    args = parser.parse_args()
    
    config = load_env()
    bot_token = config.get("TELEGRAM_BOT_TOKEN", "")
    
    if not bot_token or bot_token == "your_telegram_bot_token":
        print("❌ .env 파일에 TELEGRAM_BOT_TOKEN을 설정해주세요!")
        print("")
        print("  텔레그램 봇 만드는 방법:")
        print("  1. 텔레그램에서 @BotFather 검색")
        print("  2. /newbot 명령어 입력")
        print("  3. 봇 이름/사용자명 설정")
        print("  4. 받은 토큰을 .env 파일에 복사")
        sys.exit(1)
    
    # --setup 모드: chat_id 자동 탐색
    if args.setup:
        setup_chat_id(bot_token)
        return
    
    chat_id = config.get("TELEGRAM_CHAT_ID", "")
    if not chat_id or chat_id == "your_telegram_chat_id":
        print("❌ .env 파일에 TELEGRAM_CHAT_ID를 설정해주세요!")
        print("   자동 탐색: python scripts/notify_telegram.py --setup")
        sys.exit(1)
    
    # GitHub Pages URL
    username = config.get("GITHUB_USERNAME", "")
    repo = config.get("GITHUB_REPO_NAME", "job-report")
    
    if not username or username == "your_github_username":
        print("❌ .env 파일에 GITHUB_USERNAME을 설정해주세요!")
        sys.exit(1)
    
    now = datetime.utcnow()
    year = args.year or now.year
    week = args.week or now.isocalendar()[1]
    
    report_url = f"https://{username}.github.io/{repo}/reports/{year}-W{week}.html"
    summary = get_report_summary(year, week) or f"{year}년 {week}주차 채용공고 매칭 리포트"
    
    print(f"\n📩 텔레그램 알림 전송 중...")
    print(f"   리포트: {report_url}")
    print(f"   요약:   {summary}")
    print(f"   Chat:   {chat_id}")
    
    status, result = send_telegram_message_with_buttons(
        bot_token, chat_id, report_url, summary, year, week
    )
    
    if status == 200 and result.get("ok"):
        print(f"\n✅ 텔레그램 알림 전송 완료!")
        print(f"   텔레그램을 확인해주세요.")
    elif status == 401:
        print(f"\n❌ 봇 토큰이 유효하지 않습니다. .env 파일을 확인해주세요.")
    elif status == 400 and "chat not found" in str(result):
        print(f"\n❌ Chat ID가 유효하지 않습니다.")
        print(f"   봇에게 /start 메시지를 보낸 후 다시 시도하세요.")
        print(f"   자동 탐색: python scripts/notify_telegram.py --setup")
    else:
        print(f"\n❌ 전송 실패 (HTTP {status}): {result}")


if __name__ == "__main__":
    main()
