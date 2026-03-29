#!/bin/bash
# =============================================================================
# 채용공고 리포트 배포 스크립트
# 
# HTML 리포트 생성 → GitHub Pages에 배포 → (선택) 텔레그램 알림
#
# 사용법:
#   ./deploy.sh              # 리포트 생성 + 배포
#   ./deploy.sh --notify     # 리포트 생성 + 배포 + 텔레그램 알림
#   ./deploy.sh --skip-crawl # 크롤링 없이 기존 데이터로 리포트만 생성 + 배포
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 색상
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 인자 파싱
NOTIFY=false
SKIP_CRAWL=false
for arg in "$@"; do
    case $arg in
        --notify) NOTIFY=true ;;
        --skip-crawl) SKIP_CRAWL=true ;;
    esac
done

echo ""
echo "================================================"
echo "  📋 채용공고 리포트 배포 시작"
echo "================================================"
echo ""

# 1. (선택) 크롤링 실행
if [ "$SKIP_CRAWL" = false ]; then
    echo -e "${YELLOW}[1/4]${NC} 🕷️  크롤링 실행 중..."
    # FastAPI 서버가 실행 중인 경우 API 호출
    CRAWL_RESULT=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/crawl 2>/dev/null || echo "000")
    if [ "$CRAWL_RESULT" = "200" ]; then
        echo -e "  ${GREEN}✅ 크롤링 완료${NC}"
    else
        echo -e "  ${YELLOW}⚠️  API 서버가 실행 중이지 않습니다. 기존 데이터로 진행합니다.${NC}"
    fi
else
    echo -e "${YELLOW}[1/4]${NC} ⏭️  크롤링 스킵"
fi

# 2. HTML 리포트 생성
echo -e "${YELLOW}[2/4]${NC} 📄 HTML 리포트 생성 중..."
python3 -c "
import sys
sys.path.insert(0, '.')
from backend.database import SessionLocal
from backend.exporter import export_to_html
from datetime import datetime

db = SessionLocal()
try:
    now = datetime.utcnow()
    year = now.year
    week = now.isocalendar()[1]
    path = export_to_html(db, year, week)
except Exception as e:
    print(f'❌ 리포트 생성 실패: {e}')
    sys.exit(1)
finally:
    db.close()
"

if [ $? -ne 0 ]; then
    echo -e "  ${RED}❌ 리포트 생성 실패${NC}"
    exit 1
fi
echo -e "  ${GREEN}✅ 리포트 생성 완료${NC}"

# 3. GitHub Pages에 배포
echo -e "${YELLOW}[3/4]${NC} 🚀 GitHub Pages 배포 중..."
cd deploy

# deploy 디렉토리가 git 리포인지 확인
if [ ! -d ".git" ]; then
    echo -e "  ${YELLOW}⚠️  deploy/ 디렉토리에 Git 리포가 초기화되지 않았습니다.${NC}"
    echo ""
    echo "  다음 순서로 설정해주세요:"
    echo "  1. GitHub에 새 리포지토리 생성 (예: job-report)"
    echo "  2. 아래 명령어 실행:"
    echo ""
    echo "     cd deploy"
    echo "     git init"
    echo "     git remote add origin https://github.com/YOUR_USERNAME/job-report.git"
    echo "     git branch -M main"
    echo "     git add -A"
    echo "     git commit -m 'Initial deploy'"
    echo "     git push -u origin main"
    echo ""
    echo "  3. GitHub 리포 Settings > Pages > Source를 'main' 브랜치로 설정"
    echo ""
    cd ..
    exit 1
fi

git add -A
CHANGES=$(git status --porcelain)
if [ -z "$CHANGES" ]; then
    echo -e "  ${YELLOW}변경사항 없음. 배포 스킵.${NC}"
else
    WEEK_LABEL=$(date +%Y-W%V)
    git commit -m "📋 ${WEEK_LABEL} 리포트 업데이트"
    git push origin main
    echo -e "  ${GREEN}✅ GitHub Pages 배포 완료${NC}"
fi

cd ..

# 4. (선택) 텔레그램 알림
if [ "$NOTIFY" = true ]; then
    echo -e "${YELLOW}[4/4]${NC} 📩 텔레그램 알림 전송 중..."
    python3 scripts/notify_telegram.py
else
    echo -e "${YELLOW}[4/4]${NC} ⏭️  텔레그램 알림 스킵 (--notify 옵션으로 활성화)"
fi

echo ""
echo "================================================"
echo -e "  ${GREEN}🎉 배포 완료!${NC}"
echo "================================================"
echo ""

# .env에서 GitHub Pages URL 표시
GITHUB_USERNAME=$(grep "^GITHUB_USERNAME=" .env 2>/dev/null | cut -d'=' -f2)
GITHUB_REPO=$(grep "^GITHUB_REPO_NAME=" .env 2>/dev/null | cut -d'=' -f2)
if [ -n "$GITHUB_USERNAME" ] && [ "$GITHUB_USERNAME" != "your_github_username" ]; then
    echo "  🔗 리포트 URL: https://${GITHUB_USERNAME}.github.io/${GITHUB_REPO:-job-report}/"
    echo ""
fi
