import os
import json
import shutil
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend import models
from backend.matcher.engine import PROFILES

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
    
    - reports/ : HTML 리포트 출력 (GitHub Pages 서빙)
    """
    config = _load_env()
    pages_url = _get_pages_url(config)

    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    
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
            "matched_keywords": m.matched_keywords or "",
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
    og_description = f"웅키: {total_a}건, 쵸키: {total_b}건 매칭 | {top_companies} 등"
    report_filename = f"{year}-W{week}.html"
    og_url = f"{pages_url}/reports/{report_filename}"
    og_image_url = f"{pages_url}/og-image.png"

    # 데이터에 matched_keyword 추가 (이미 위에서 수집됨)
    data_a_json = json.dumps(job_data_a, ensure_ascii=False)
    data_b_json = json.dumps(job_data_b, ensure_ascii=False)
    stats_json  = json.dumps(stats_list, ensure_ascii=False)
    profiles_json = json.dumps(PROFILES, ensure_ascii=False)

    total_collected = sum(s["count"] for s in stats_list)
    generated_at = datetime.utcnow().strftime('%Y.%m.%d %H:%M')

    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>웅키와 쵸키의 이직 프로젝트</title>
    <meta name="description" content="{og_description}">
    <meta property="og:title" content="📋 {year}년 {week}주차 채용공고 매칭 리포트" />
    <meta property="og:description" content="{og_description}" />
    <meta property="og:image" content="{og_image_url}" />
    <meta property="og:url" content="{og_url}" />
    <meta property="og:type" content="website" />
    <meta property="og:locale" content="ko_KR" />
    <meta property="og:updated_time" content="{datetime.utcnow().isoformat()}" />
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: 'Pretendard', -apple-system, sans-serif; background: #fff; color: #111; }}

.top-bar {{ display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; border-bottom: 1px solid #111; max-width: 680px; margin: 0 auto; }}
.logo {{ font-size: 13px; font-weight: 800; letter-spacing: -0.3px; }}
.date-tag {{ font-size: 11px; color: #888; border: 1px solid #ddd; border-radius: 3px; padding: 2px 7px; }}

.hero {{ max-width: 680px; margin: 0 auto; padding: 28px 24px 20px; border-bottom: 2px solid #111; }}
.hero-label {{ font-size: 10px; font-weight: 700; letter-spacing: 2px; color: #aaa; text-transform: uppercase; margin-bottom: 8px; }}
.hero-title {{ font-size: 28px; font-weight: 800; letter-spacing: -1px; line-height: 1.2; }}
.hero-sub {{ font-size: 13px; color: #888; margin-top: 10px; }}
.hero-counts {{ display: flex; gap: 16px; margin-top: 16px; }}
.count-chip {{ font-size: 12px; font-weight: 700; padding: 5px 12px; border-radius: 20px; cursor: pointer; border: 1.5px solid #ddd; color: #888; transition: all 0.15s; }}
.count-chip.active {{ background: #111; color: #fff; border-color: #111; }}

.content {{ max-width: 680px; margin: 0 auto; padding: 0 24px 60px; }}

.keyword-panel {{ margin-top: 20px; border: 1px solid #ebebeb; border-radius: 8px; overflow: hidden; }}
.keyword-panel-header {{ display: flex; justify-content: space-between; align-items: center; padding: 11px 14px; cursor: pointer; background: #fafafa; user-select: none; }}
.keyword-panel-header:hover {{ background: #f4f4f4; }}
.keyword-panel-title {{ font-size: 11px; font-weight: 700; letter-spacing: 1px; color: #888; text-transform: uppercase; }}
.kw-toggle {{ font-size: 11px; color: #bbb; transition: transform 0.2s; display: inline-block; }}
.kw-toggle.open {{ transform: rotate(180deg); }}
.keyword-body {{ padding: 14px; border-top: 1px solid #ebebeb; display: none; }}
.keyword-body.open {{ display: block; }}
.kw-group {{ display: flex; gap: 10px; align-items: flex-start; margin-bottom: 10px; }}
.kw-group:last-child {{ margin-bottom: 0; }}
.kw-group-label {{ font-size: 10px; font-weight: 700; color: #bbb; letter-spacing: 0.5px; min-width: 32px; padding-top: 3px; flex-shrink: 0; }}
.kw-chips {{ display: flex; flex-wrap: wrap; gap: 5px; }}
.kw-chip {{ font-size: 11px; color: #555; background: #f2f2f2; border-radius: 4px; padding: 2px 7px; font-weight: 500; }}
.kw-note {{ font-size: 11px; color: #bbb; margin-top: 10px; padding-top: 10px; border-top: 1px solid #f0f0f0; }}

.list-header {{ display: flex; justify-content: space-between; align-items: center; padding: 16px 0 10px; border-bottom: 1px solid #111; margin-top: 20px; }}
.list-header-left {{ font-size: 11px; font-weight: 700; letter-spacing: 1px; color: #aaa; text-transform: uppercase; }}
.list-header-right {{ font-size: 11px; color: #aaa; }}

.job-row {{ display: grid; grid-template-columns: 1fr auto; align-items: center; gap: 12px; padding: 14px 0; border-bottom: 1px solid #f0f0f0; }}
.job-row:hover {{ background: #fafafa; margin: 0 -8px; padding: 14px 8px; border-radius: 4px; }}
.job-name {{ font-size: 15px; font-weight: 700; color: #111; line-height: 1.3; word-break: keep-all; }}
.job-meta {{ display: flex; gap: 8px; align-items: center; margin-top: 5px; flex-wrap: wrap; }}
.meta-co {{ font-size: 12px; color: #aaa; }}
.meta-sep {{ font-size: 12px; color: #ddd; }}
.meta-dl {{ font-size: 12px; color: #bbb; }}
.meta-dl.urgent {{ color: #e03131; font-weight: 600; }}
.meta-keyword {{ font-size: 10px; color: #888; background: #f0f0f0; border-radius: 3px; padding: 1px 6px; font-weight: 600; }}
.urgent-tag {{ font-size: 10px; font-weight: 800; color: #e03131; letter-spacing: 0.5px; padding: 2px 5px; border: 1.5px solid #e03131; border-radius: 3px; white-space: nowrap; }}
.row-right {{ display: flex; flex-direction: column; align-items: flex-end; gap: 6px; }}
.go-link {{ font-size: 11px; font-weight: 700; color: #111; text-decoration: none; letter-spacing: 0.5px; white-space: nowrap; }}
.go-link:hover {{ text-decoration: underline; }}

.stats-section {{ margin-top: 20px; }}
.stats-row {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #f0f0f0; }}
.stats-bar-wrap {{ margin-top: 6px; height: 4px; background: #f0f0f0; border-radius: 2px; overflow: hidden; }}
.stats-bar-fill {{ height: 100%; background: #111; border-radius: 2px; }}
.empty-state {{ text-align: center; padding: 80px 0; color: #ccc; font-size: 14px; }}
.footer {{ text-align: center; padding: 32px 20px; font-size: 12px; color: #ccc; border-top: 1px solid #f0f0f0; margin-top: 20px; }}
    </style>
</head>
<body>

<div class="top-bar">
    <div class="logo">웅키와 쵸키의 이직 프로젝트</div>
    <div class="date-tag">{year} W{week}</div>
</div>

<div class="hero">
    <div class="hero-label">Weekly Job Report</div>
    <div class="hero-title">이번 주<br>채용 매칭 결과</div>
    <div class="hero-sub">총 {total_collected}건 수집 · 웅키 {total_a}건, 쵸키 {total_b}건 매칭</div>
    <div class="hero-counts">
        <div class="count-chip active" onclick="show('A', this)">웅키 {total_a}</div>
        <div class="count-chip" onclick="show('B', this)">쵸키 {total_b}</div>
        <div class="count-chip" onclick="show('S', this)">통계</div>
    </div>
</div>

<div class="content" id="content"></div>

<div class="footer">자동 생성됨 · {generated_at} UTC</div>

<script>
    const dataA = {data_a_json};
    const dataB = {data_b_json};
    const stats = {stats_json};
    const profiles = {profiles_json};

    let kwOpen = false;

    function toggleKw() {{
        kwOpen = !kwOpen;
        const body = document.getElementById('kw-body');
        const toggle = document.getElementById('kw-toggle');
        if (body) body.classList.toggle('open', kwOpen);
        if (toggle) toggle.classList.toggle('open', kwOpen);
    }}

    function renderKeywordPanel(profileKey) {{
        const groups = profiles[profileKey]?.sub_groups || {{}};
        const rows = Object.entries(groups).map(([label, kws]) => `
            <div class="kw-group">
                <span class="kw-group-label">${{label}}</span>
                <div class="kw-chips">${{kws.map(k => `<span class="kw-chip">${{k}}</span>`).join('')}}</div>
            </div>
        `).join('');
        return `
            <div class="keyword-panel">
                <div class="keyword-panel-header" onclick="toggleKw()">
                    <span class="keyword-panel-title">매칭 키워드</span>
                    <span class="kw-toggle" id="kw-toggle">▼</span>
                </div>
                <div class="keyword-body" id="kw-body">
                    ${{rows}}
                    <div class="kw-note">* 인턴 · Intern 공고는 제외됩니다</div>
                </div>
            </div>
        `;
    }}

    function renderRows(list) {{
        return list.map(j => `
            <div class="job-row">
                <div>
                    <div class="job-name">${{j.title}}</div>
                    <div class="job-meta">
                        <span class="meta-co">${{j.company}}</span>
                        <span class="meta-sep">·</span>
                        <span class="meta-dl ${{j.urgent ? 'urgent' : ''}}">${{j.deadline}}</span>
                        ${{j.matched_keywords ? `<span class="meta-keyword">${{j.matched_keywords.split(',')[0].trim()}}</span>` : ''}}
                    </div>
                </div>
                <div class="row-right">
                    ${{j.urgent ? '<span class="urgent-tag">URGENT</span>' : ''}}
                    <a class="go-link" href="${{j.url}}" target="_blank" rel="noopener">보기 →</a>
                </div>
            </div>
        `).join('');
    }}

    function show(key, el) {{
        document.querySelectorAll('.count-chip').forEach(c => c.classList.remove('active'));
        el.classList.add('active');
        kwOpen = false;
        const content = document.getElementById('content');

        if (key === 'S') {{
            const total = stats.reduce((acc, s) => acc + s.count, 0);
            const maxCount = stats.length > 0 ? stats[0].count : 1;
            content.innerHTML = `
                <div class="stats-section">
                    <div class="list-header" style="margin-top:0">
                        <span class="list-header-left">사이트별 수집</span>
                        <span class="list-header-right">총 ${{total}}건</span>
                    </div>
                    ${{stats.map(s => `
                        <div class="stats-row">
                            <div style="flex:1">
                                <div style="display:flex;justify-content:space-between;font-size:13px;font-weight:600">
                                    <span>${{s.name}}</span><span style="color:#aaa;font-weight:400">${{s.count}}건</span>
                                </div>
                                <div class="stats-bar-wrap">
                                    <div class="stats-bar-fill" style="width:${{Math.round(s.count/maxCount*100)}}%"></div>
                                </div>
                            </div>
                        </div>
                    `).join('')}}
                    <div class="list-header">
                        <span class="list-header-left">프로필별 매칭</span>
                    </div>
                    <div class="stats-row">
                        <span style="font-size:13px;font-weight:600">웅키 (마케팅)</span>
                        <span style="font-size:13px;color:#aaa">${{dataA.length}}건</span>
                    </div>
                    <div class="stats-row">
                        <span style="font-size:13px;font-weight:600">쵸키 (서비스 운영 기획)</span>
                        <span style="font-size:13px;color:#aaa">${{dataB.length}}건</span>
                    </div>
                </div>
            `;
            return;
        }}

        const jobs = key === 'A' ? dataA : dataB;
        const profileKey = key === 'A' ? '웅키' : '쵸키';
        const urgent = jobs.filter(j => j.urgent);
        const normal = jobs.filter(j => !j.urgent);

        if (jobs.length === 0) {{
            content.innerHTML = renderKeywordPanel(profileKey) + `<div class="empty-state">매칭된 공고가 없습니다.</div>`;
            return;
        }}

        content.innerHTML = `
            ${{renderKeywordPanel(profileKey)}}
            ${{urgent.length ? `
                <div class="list-header">
                    <span class="list-header-left">마감임박</span>
                    <span class="list-header-right">${{urgent.length}}건</span>
                </div>
                ${{renderRows(urgent)}}
            ` : ''}}
            <div class="list-header" style="margin-top:${{urgent.length ? '12px' : '0'}}">
                <span class="list-header-left">전체 공고</span>
                <span class="list-header-right">${{normal.length}}건</span>
            </div>
            ${{renderRows(normal)}}
        `;
    }}

    show('A', document.querySelector('.count-chip.active'));
</script>
</body>
</html>"""
    
    # reports/ 에 저장
    report_filename = f"{year}-W{week}.html"
    report_path = os.path.join(reports_dir, report_filename)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # latest.html 덮어쓰기 (항상 최신)
    latest_path = os.path.join(reports_dir, "latest.html")
    shutil.copy2(report_path, latest_path)

    print(f"✅ HTML 리포트 생성 완료:")
    print(f"   리포트: {report_path}")
    print(f"   최신:   {latest_path}")

    return report_path
