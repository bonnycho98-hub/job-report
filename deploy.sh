#!/bin/bash

# =============================================================================
# 채용공고 리포트 배포 스크립트 (로컬 & 텔레그램 전용 지원)
# 
# 사용법:
#   ./deploy.sh --notify               # 배포 + 텔레그램 알림
#   ./deploy.sh --notify --skip-push   # 배포 안 함 + 텔레그램 알림만 (로컬 전용)
# =============================================================================

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

NOTIFY=false
SKIP_CRAWL=false
SKIP_PUSH=false

# 인자 처리
for arg in "$@"; do
  case $arg in
    --notify) NOTIFY=true ;;
    --skip-crawl) SKIP_CRAWL=true ;;
    --skip-push) SKIP_PUSH=true ;;
  esac
done

echo -e "${GREEN}================================================"
echo -e "  🚀 채용공고 리포트 실행 시작 (로컬 전용 모드 지원)"
echo -e "================================================${NC}"

# 1. 크롤링 수행
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
    print('  ✅ 리포트 생성 완료')
except Exception as e:
    print(f'  ❌ 생성 실패: {e}')
finally:
    db.close()
"

# 3. GitHub Pages 배포 (옵션)
if [ "$SKIP_PUSH" = true ]; then
    echo -e "${YELLOW}[3/4]${NC} ⏭️  GitHub 배포 스킵 (로컬 전용)"
else
    echo -e "${YELLOW}[3/4]${NC} 🚀 GitHub Pages 배포 중..."
    cd deploy
    git add .
    git commit -m "📋 리포트 업데이트 ($(date +'%Y-%m-%d'))" || echo "No changes to commit"
    git push origin main
    cd ..
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
