#!/bin/bash

# =============================================================================
# 채용공고 리포트 배포 스크립트
#
# 사용법:
#   ./deploy.sh                        # 크롤링 + 리포트 생성만
#   ./deploy.sh --notify               # + 텔레그램 알림
#   ./deploy.sh --skip-crawl           # 크롤링 스킵
#   ./deploy.sh --skip-push            # GitHub 배포 스킵
# =============================================================================

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

NOTIFY=false
SKIP_CRAWL=false
SKIP_PUSH=false

for arg in "$@"; do
  case $arg in
    --notify) NOTIFY=true ;;
    --skip-crawl) SKIP_CRAWL=true ;;
    --skip-push) SKIP_PUSH=true ;;
  esac
done

echo -e "${GREEN}================================================"
echo -e "  🚀 채용공고 리포트 실행"
echo -e "================================================${NC}"

# 1. 크롤링
if [ "$SKIP_CRAWL" = true ]; then
    echo -e "${YELLOW}[1/4]${NC} ⏭️  크롤링 스킵"
else
    echo -e "${YELLOW}[1/4]${NC} 🕷️  채용공고 크롤링 중..."
    source venv/bin/activate
    PYTHONPATH=. python3 backend/main.py --trigger
    echo -e "  ✅ 크롤링 및 매칭 완료"
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
    export_to_html(db, now.year, now.isocalendar()[1])
except Exception as e:
    print(f'  ❌ 생성 실패: {e}')
finally:
    db.close()
"

# 3. GitHub Pages 배포
if [ "$SKIP_PUSH" = true ]; then
    echo -e "${YELLOW}[3/4]${NC} ⏭️  GitHub 배포 스킵"
else
    echo -e "${YELLOW}[3/4]${NC} 🚀 GitHub Pages 배포 중..."
    git add reports/ .nojekyll index.html
    git commit -m "📋 리포트 업데이트 ($(date +'%Y-%m-%d'))" || echo "  변경사항 없음"
    git push origin main
    echo -e "  ✅ GitHub Pages 배포 완료"
fi

# 4. 텔레그램 알림
if [ "$NOTIFY" = true ]; then
    echo -e "${YELLOW}[4/4]${NC} 📩 텔레그램 알림 전송 중..."
    python3 scripts/notify_telegram.py
else
    echo -e "${YELLOW}[4/4]${NC} ⏭️  텔레그램 알림 스킵"
fi

echo -e "\n${GREEN}================================================"
echo -e "  🎉 작업 완료!"
echo -e "================================================${NC}"
