import os
import json
import shutil
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend import models

# .env 파일에서 설정 로드
def _load_env():
    """프로젝트 루트의 .env 파일에서 설정값을 읽어옵니다."""
    config = {}
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()
    return config


def _get_pages_url(config):
    """GitHub Pages URL을 생성합니다."""
    username = config.get("GITHUB_USERNAME", "your_github_username")
    repo = config.get("GITHUB_REPO_NAME", "job-report")
    return f"https://{username}.github.io/{repo}"


def _parse_deadline(deadline_str):
    """마감일 문자열을 파싱하여 날짜 비교가 가능하도록 합니다."""
    if not deadline_str:
        return None
    # "2026.03.29" 또는 "2026.03.25 ~ 2026.04.08" 형태 처리
    try:
        # "~" 가 포함된 경우 끝 날짜 사용
        if "~" in deadline_str:
            end_part = deadline_str.split("~")[-1].strip()
        elif "채용시까지" in deadline_str or "상시" in deadline_str or "영입종료" in deadline_str or "마감" in deadline_str:
            return None
        else:
            end_part = deadline_str.strip()
        
        # 다양한 날짜 포맷 시도
        for fmt in ["%Y.%m.%d", "%Y-%m-%d", "%Y/%m/%d"]:
            try:
                return datetime.strptime(end_part, fmt)
            except ValueError:
                continue
    except Exception:
        pass
    return None


def _is_deadline_soon(deadline_str, days=3):
    """마감일이 n일 이내인지 확인합니다."""
    deadline = _parse_deadline(deadline_str)
    if deadline is None:
        return False
    now = datetime.utcnow()
    return now <= deadline <= now + timedelta(days=days)


def export_to_html(db: Session, year: int, week: int) -> str:
    """
    주어진 주차(week)의 매칭 결과를 조회하여 프리미엄 모바일 디자인이 적용된
    단일 HTML 파일(CSS/JS 포함)로 렌더링 후 저장합니다.
    
    - output/  : 기존 호환을 위한 로컬 출력
    - deploy/reports/ : GitHub Pages 배포용 출력
    """
    config = _load_env()
    pages_url = _get_pages_url(config)
    kakao_js_key = config.get("KAKAO_JS_KEY", "YOUR_KAKAO_JS_KEY_HERE")
    
    output_dir = "output"
    deploy_dir = os.path.join("deploy", "reports")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(deploy_dir, exist_ok=True)
    
    # 해당 주차의 매칭 결과 가져오기
    matches = db.query(models.MatchResult).filter(
        models.MatchResult.year == year,
        models.MatchResult.week_number == week
    ).all()
    
    # 데이터 직렬화 (JS에서 사용하기 위함)
    job_data_a = []
    job_data_b = []
    site_stats = {}
    
    for m in matches:
        jp = m.job_posting
        # 사이트별 통계 계산
        site_name = jp.site.name if jp.site else "기타"
        site_stats[site_name] = site_stats.get(site_name, 0) + 1
        
        deadline_str = jp.deadline or "상시채용"
        job_item = {
            "company": jp.company,
            "title": jp.title,
            "position": jp.position,
            "url": jp.source_url,
            "score": m.match_score,
            "sub_group": m.sub_group,
            "deadline": deadline_str,
            "urgent": _is_deadline_soon(deadline_str)
        }
        if m.profile_id == 1:
            job_data_a.append(job_item)
        else:
            job_data_b.append(job_item)

    # 사이트 통계를 리스트 형태로 변환
    stats_list = [{"name": k, "count": v} for k, v in sorted(site_stats.items(), key=lambda x: x[1], reverse=True)]

    # OG 메타태그용 요약 텍스트
    total_a = len(job_data_a)
    total_b = len(job_data_b)
    top_companies = ", ".join([s["name"] for s in stats_list[:3]])
    og_description = f"프로필 A: {total_a}건, 프로필 B: {total_b}건 매칭 | {top_companies} 등"
    report_filename = f"{year}-W{week}.html"
    og_url = f"{pages_url}/reports/{report_filename}"
    og_image_url = f"{pages_url}/og-image.png"

    # 프리미엄 CSS
    premium_css = """
    :root {
      --primary: #3182f6; --primary-light: #e8f3ff; --bg-color: #f2f4f6; --card-bg: #ffffff;
      --text-main: #191f28; --text-sub: #4e5968; --text-mute: #8b95a1;
      --radius-xl: 24px; --shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
      --urgent: #ff6b6b; --urgent-bg: #fff5f5;
    }
    * { box-sizing: border-box; }
    body { font-family: -apple-system, 'Pretendard', sans-serif; background: var(--bg-color); color: var(--text-main); margin: 0; padding-bottom: 30px; -webkit-font-smoothing: antialiased; }
    header { position: sticky; top: 0; background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); z-index: 100; padding: 16px 20px; border-bottom: 1px solid #eceef0; }
    .header-top { display: flex; justify-content: space-between; align-items: center; }
    .header-title { font-weight: 700; font-size: 18px; }
    .header-date { font-size: 13px; color: var(--text-mute); }
    .tabs { display: flex; gap: 6px; margin-top: 12px; }
    .tab { padding: 8px 16px; font-size: 14px; font-weight: 600; color: var(--text-mute); cursor: pointer; border-radius: 20px; border: none; background: transparent; transition: all 0.2s ease; }
    .tab.active { color: #fff; background: var(--text-main); }
    .tab:not(.active):hover { background: #eceef0; }
    .tab .count { display: inline-block; margin-left: 4px; padding: 1px 6px; border-radius: 10px; font-size: 11px; font-weight: 700; background: var(--primary-light); color: var(--primary); }
    .tab.active .count { background: rgba(255,255,255,0.2); color: #fff; }
    .container { padding: 16px; max-width: 500px; margin: 0 auto; }
    .card { background: var(--card-bg); border-radius: var(--radius-xl); padding: 20px; margin-bottom: 12px; box-shadow: var(--shadow); transition: transform 0.15s ease; }
    .card:active { transform: scale(0.98); }
    .card.urgent { border-left: 3px solid var(--urgent); }
    .job-item { display: flex; align-items: flex-start; gap: 12px; }
    .job-icon { width: 44px; height: 44px; border-radius: 12px; background: var(--primary-light); display: flex; align-items: center; justify-content: center; color: var(--primary); font-size: 18px; flex-shrink: 0; }
    .card.urgent .job-icon { background: var(--urgent-bg); color: var(--urgent); }
    .job-info { flex: 1; min-width: 0; }
    .job-company { font-size: 13px; color: var(--text-sub); font-weight: 500; }
    .job-title { font-weight: 600; font-size: 15px; margin-top: 2px; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
    .job-meta { display: flex; align-items: center; gap: 8px; margin-top: 6px; flex-wrap: wrap; }
    .badge { padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 600; text-decoration: none; }
    .badge-score { background: var(--primary-light); color: var(--primary); }
    .badge-group { background: #f2f4f6; color: var(--text-sub); }
    .badge-urgent { background: var(--urgent-bg); color: var(--urgent); animation: pulse 2s infinite; }
    .badge-deadline { background: #f2f4f6; color: var(--text-mute); font-weight: 500; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
    .card-actions { display: flex; justify-content: flex-end; margin-top: 12px; gap: 8px; }
    .btn-view { display: inline-flex; align-items: center; gap: 4px; padding: 6px 14px; border-radius: 8px; font-size: 13px; font-weight: 600; background: var(--primary); color: #fff; text-decoration: none; border: none; cursor: pointer; transition: opacity 0.15s; }
    .btn-view:hover { opacity: 0.85; }
    .btn-share { display: inline-flex; align-items: center; padding: 6px 10px; border-radius: 8px; font-size: 16px; background: #fee500; color: #3c1e1e; border: none; cursor: pointer; transition: opacity 0.15s; }
    .btn-share:hover { opacity: 0.85; }
    .stats-item { display: flex; justify-content: space-between; align-items: center; padding: 14px 0; border-bottom: 1px solid #f2f4f6; }
    .stats-item:last-child { border-bottom: none; }
    .stats-bar { height: 4px; border-radius: 2px; background: var(--primary); margin-top: 6px; transition: width 0.5s ease; }
    .empty-state { text-align: center; padding: 60px 20px; color: var(--text-mute); }
    .empty-state i { font-size: 48px; margin-bottom: 16px; display: block; opacity: 0.3; }
    .footer { text-align: center; padding: 20px; font-size: 12px; color: var(--text-mute); }
    """

    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{year}년 {week}주차 채용공고 매칭 리포트</title>
    
    <!-- SEO & OG 메타태그 (카카오톡/SNS 프리뷰용) -->
    <meta name="description" content="{og_description}">
    <meta property="og:title" content="📋 {year}년 {week}주차 채용공고 매칭 리포트" />
    <meta property="og:description" content="{og_description}" />
    <meta property="og:image" content="{og_image_url}" />
    <meta property="og:url" content="{og_url}" />
    <meta property="og:type" content="website" />
    <meta property="og:locale" content="ko_KR" />
    
    <!-- 카카오톡 캐시 방지 -->
    <meta property="og:updated_time" content="{datetime.utcnow().isoformat()}" />
    
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>{premium_css}</style>
</head>
<body>
    <header>
        <div class="header-top">
            <span class="header-title">📋 Job Finder Report</span>
            <span class="header-date">{year}년 {week}주차</span>
        </div>
        <div class="tabs">
            <button class="tab active" onclick="switchTab('A', this)">
                프로필 A <span class="count" id="count-a">0</span>
            </button>
            <button class="tab" onclick="switchTab('B', this)">
                프로필 B <span class="count" id="count-b">0</span>
            </button>
            <button class="tab" onclick="switchTab('STATS', this)">
                📊 분석
            </button>
        </div>
    </header>

    <div class="container" id="content-area"></div>
    
    <div class="footer">
        Job Finder Report · 자동 생성됨 · {datetime.utcnow().strftime('%Y.%m.%d %H:%M')} UTC
    </div>

    <script>
        const dataA = {json.dumps(job_data_a, ensure_ascii=False)};
        const dataB = {json.dumps(job_data_b, ensure_ascii=False)};
        const stats = {json.dumps(stats_list, ensure_ascii=False)};

        // 카운트 표시
        document.getElementById('count-a').textContent = dataA.length;
        document.getElementById('count-b').textContent = dataB.length;

        function switchTab(type, el) {{
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            el.classList.add('active');
            if (type === 'STATS') {{
                renderStats();
            }} else {{
                renderJobs(type === 'A' ? dataA : dataB);
            }}
        }}

        function renderJobs(jobs) {{
            const container = document.getElementById('content-area');
            if (jobs.length === 0) {{
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fa-solid fa-inbox"></i>
                        <p>매칭된 공고가 없습니다.</p>
                    </div>`;
                return;
            }}
            
            // 긴급(마감 임박) 공고를 상단에 배치
            const sorted = [...jobs].sort((a, b) => {{
                if (a.urgent && !b.urgent) return -1;
                if (!a.urgent && b.urgent) return 1;
                return b.score - a.score;
            }});
            
            container.innerHTML = sorted.map(job => `
                <div class="card ${{job.urgent ? 'urgent' : ''}}">
                    <div class="job-item">
                        <div class="job-icon">
                            <i class="fa-solid ${{job.urgent ? 'fa-fire' : 'fa-building'}}"></i>
                        </div>
                        <div class="job-info">
                            <div class="job-company">${{job.company}}</div>
                            <div class="job-title">${{job.title}}</div>
                            <div class="job-meta">
                                <span class="badge badge-score">${{job.score}}점</span>
                                <span class="badge badge-group">${{job.sub_group}}</span>
                                ${{job.urgent ? '<span class="badge badge-urgent">🔥 마감임박</span>' : ''}}
                                <span class="badge badge-deadline">${{job.deadline}}</span>
                            </div>
                        </div>
                    </div>
                    <div class="card-actions">
                        <button class="btn-share" onclick="shareUrl('${{job.title}}', '${{job.company}}', '${{job.url}}')" title="공유">
                            <i class="fa-solid fa-share-nodes"></i>
                        </button>
                        <a href="${{job.url}}" target="_blank" rel="noopener" class="btn-view">
                            공고 보기 <i class="fa-solid fa-arrow-up-right-from-square"></i>
                        </a>
                    </div>
                </div>
            `).join('');
        }}

        function renderStats() {{
            const container = document.getElementById('content-area');
            const total = stats.reduce((acc, curr) => acc + curr.count, 0);
            const maxCount = stats.length > 0 ? stats[0].count : 1;
            
            container.innerHTML = `
                <div class="card">
                    <div style="font-weight:700; font-size:18px; margin-bottom:4px;">사이트별 수집 현황</div>
                    <div style="font-size:14px; color:var(--text-sub); margin-bottom:20px;">
                        이번 주 총 <span style="color:var(--primary); font-weight:700;">${{total}}</span>건의 공고를 수집했습니다.
                    </div>
                    <div>
                        ${{stats.map(s => `
                            <div class="stats-item">
                                <div style="flex:1;">
                                    <div style="display:flex; justify-content:space-between; align-items:center;">
                                        <span style="font-size:14px; font-weight:500;">${{s.name}}</span>
                                        <span style="font-size:14px; font-weight:700; color:var(--primary);">${{s.count}}건</span>
                                    </div>
                                    <div class="stats-bar" style="width:${{Math.round(s.count / maxCount * 100)}}%;"></div>
                                </div>
                            </div>
                        `).join('')}}
                    </div>
                </div>
                <div class="card">
                    <div style="font-weight:700; font-size:16px; margin-bottom:12px;">📊 프로필별 매칭 요약</div>
                    <div class="stats-item">
                        <span style="font-size:14px; font-weight:500;">프로필 A (마케팅)</span>
                        <span style="font-size:14px; font-weight:700; color:var(--primary);">${{dataA.length}}건</span>
                    </div>
                    <div class="stats-item">
                        <span style="font-size:14px; font-weight:500;">프로필 B (서비스 운영 기획)</span>
                        <span style="font-size:14px; font-weight:700; color:var(--primary);">${{dataB.length}}건</span>
                    </div>
                </div>
            `;
        }}

        function shareUrl(title, company, url) {{
            // Web Share API 시도 (모바일에서 카카오톡 등 선택 가능)
            if (navigator.share) {{
                navigator.share({{
                    title: '[채용공고] ' + company,
                    text: title,
                    url: url
                }}).catch(() => {{}});
            }} else {{
                // 데스크톱 폴백: 클립보드에 복사
                navigator.clipboard.writeText(url).then(() => {{
                    alert('URL이 클립보드에 복사되었습니다!');
                }}).catch(() => {{
                    prompt('URL을 복사하세요:', url);
                }});
            }}
        }}

        // 초기 로드
        window.onload = () => renderJobs(dataA);
    </script>
</body>
</html>"""
    
    # 1. 기존 output/ 에 저장 (호환성)
    premium_filename = f"{year}-W{week}-Premium.html"
    premium_path = os.path.join(output_dir, premium_filename)
    with open(premium_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # 2. deploy/reports/ 에 저장 (GitHub Pages 배포용)
    deploy_filename = f"{year}-W{week}.html"
    deploy_path = os.path.join(deploy_dir, deploy_filename)
    with open(deploy_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # 3. deploy/reports/latest.html 로 덮어쓰기 (항상 최신)
    latest_path = os.path.join(deploy_dir, "latest.html")
    shutil.copy2(deploy_path, latest_path)
    
    print(f"✅ HTML 리포트 생성 완료:")
    print(f"   로컬: {premium_path}")
    print(f"   배포: {deploy_path}")
    print(f"   최신: {latest_path}")
        
    return premium_path
