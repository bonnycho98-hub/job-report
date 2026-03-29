#!/usr/bin/env python3
"""
카카오 OAuth2 인증 헬퍼 스크립트

최초 1회 실행하여 카카오 로그인 → Access Token + Refresh Token 획득.
이후에는 Refresh Token으로 자동 갱신됩니다.

사용법:
    python scripts/kakao_auth.py

사전 준비:
    1. https://developers.kakao.com 에서 앱 생성
    2. [앱 설정 > 플랫폼] 에서 Web 플랫폼 추가: http://localhost:9999
    3. [제품 설정 > 카카오 로그인] 활성화
    4. [제품 설정 > 카카오 로그인 > Redirect URI] 에 http://localhost:9999/callback 추가
    5. [제품 설정 > 카카오 로그인 > 동의항목] 에서 "카카오톡 메시지 전송" 항목 동의
    6. .env 파일에 KAKAO_REST_API_KEY 설정
"""

import os
import sys
import json
import webbrowser
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

# 프로젝트 루트 기준으로 .env 파일 경로
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")


def load_env():
    """프로젝트 .env 파일 로드"""
    config = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()
    return config


def save_env(config):
    """프로젝트 .env 파일 저장 (기존 주석 보존)"""
    lines = []
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r") as f:
            lines = f.readlines()
    
    # 기존 키-값 업데이트
    updated_keys = set()
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in config:
                new_lines.append(f"{key}={config[key]}\n")
                updated_keys.add(key)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    # 새 키 추가
    for key, value in config.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={value}\n")
    
    with open(ENV_PATH, "w") as f:
        f.writelines(new_lines)


class CallbackHandler(BaseHTTPRequestHandler):
    """OAuth2 콜백을 처리하는 임시 HTTP 서버"""
    auth_code = None
    
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        if "code" in params:
            CallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                "<html><body style='font-family:sans-serif;text-align:center;padding:60px;'>"
                "<h2>✅ 카카오 인증 완료!</h2>"
                "<p>이 창을 닫아도 됩니다.</p>"
                "</body></html>".encode("utf-8")
            )
        else:
            error = params.get("error_description", ["알 수 없는 오류"])[0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"<h2>❌ 인증 실패: {error}</h2>".encode("utf-8"))
    
    def log_message(self, format, *args):
        pass  # 로그 숨김


def get_authorization_code(rest_api_key, redirect_uri):
    """브라우저를 열어 카카오 로그인 → Authorization Code 획득"""
    auth_url = (
        f"https://kauth.kakao.com/oauth/authorize"
        f"?client_id={rest_api_key}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=talk_message"
    )
    
    print(f"\n🔐 카카오 로그인 페이지를 엽니다...")
    print(f"   URL: {auth_url}\n")
    webbrowser.open(auth_url)
    
    # 콜백 대기
    port = int(redirect_uri.split(":")[-1].split("/")[0])
    server = HTTPServer(("localhost", port), CallbackHandler)
    print(f"⏳ 카카오 로그인 완료를 기다리는 중... (localhost:{port})")
    
    while CallbackHandler.auth_code is None:
        server.handle_request()
    
    server.server_close()
    return CallbackHandler.auth_code


def get_tokens(rest_api_key, redirect_uri, auth_code):
    """Authorization Code로 Access Token + Refresh Token 획득"""
    url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": rest_api_key,
        "redirect_uri": redirect_uri,
        "code": auth_code,
    }
    
    response = requests.post(url, data=data)
    result = response.json()
    
    if "access_token" not in result:
        print(f"❌ 토큰 발급 실패: {result}")
        sys.exit(1)
    
    return result["access_token"], result["refresh_token"]


def refresh_access_token(rest_api_key, refresh_token):
    """Refresh Token으로 Access Token 갱신"""
    url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": rest_api_key,
        "refresh_token": refresh_token,
    }
    
    response = requests.post(url, data=data)
    result = response.json()
    
    if "access_token" not in result:
        return None, None
    
    new_refresh = result.get("refresh_token", refresh_token)
    return result["access_token"], new_refresh


def main():
    config = load_env()
    rest_api_key = config.get("KAKAO_REST_API_KEY", "")
    redirect_uri = config.get("KAKAO_REDIRECT_URI", "http://localhost:9999/callback")
    
    if not rest_api_key or rest_api_key == "your_kakao_rest_api_key":
        print("❌ .env 파일에 KAKAO_REST_API_KEY를 설정해주세요!")
        print("   카카오 개발자 사이트: https://developers.kakao.com")
        sys.exit(1)
    
    existing_refresh = config.get("KAKAO_REFRESH_TOKEN", "")
    
    if existing_refresh:
        print("🔄 기존 Refresh Token으로 Access Token 갱신 시도...")
        access_token, new_refresh = refresh_access_token(rest_api_key, existing_refresh)
        
        if access_token:
            config["KAKAO_ACCESS_TOKEN"] = access_token
            if new_refresh:
                config["KAKAO_REFRESH_TOKEN"] = new_refresh
            save_env(config)
            print(f"✅ Access Token 갱신 완료!")
            print(f"   .env 파일에 저장되었습니다.")
            return
        else:
            print("⚠️  Refresh Token 만료됨. 재인증이 필요합니다.")
    
    # 새로 인증
    auth_code = get_authorization_code(rest_api_key, redirect_uri)
    print(f"\n✅ Authorization Code 획득: {auth_code[:10]}...")
    
    access_token, refresh_token = get_tokens(rest_api_key, redirect_uri, auth_code)
    
    config["KAKAO_ACCESS_TOKEN"] = access_token
    config["KAKAO_REFRESH_TOKEN"] = refresh_token
    save_env(config)
    
    print(f"\n🎉 카카오 인증 완료!")
    print(f"   Access Token:  {access_token[:20]}...")
    print(f"   Refresh Token: {refresh_token[:20]}...")
    print(f"   .env 파일에 저장되었습니다.")


if __name__ == "__main__":
    main()
