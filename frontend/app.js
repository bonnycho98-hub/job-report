const API_BASE = '/api';
let currentProfile = 'A';
let allResults = [];        // 전체 결과 캐시
let currentCompany = null;  // 현재 선택된 회사 필터

// ─── Navigation ────────────────────────────────────────────────
function switchTab(view) {
    document.getElementById('view-dashboard').classList.toggle('hidden', view !== 'dashboard');
    document.getElementById('view-settings').classList.toggle('hidden', view !== 'settings');
    document.getElementById('view-logs').classList.toggle('hidden', view !== 'logs');

    const activeNav = 'h-full px-3 text-xs font-medium text-gray-900 border-b-2 border-gray-900 transition-colors focus:outline-none';
    const inactiveNav = 'h-full px-3 text-xs font-medium text-gray-400 border-b-2 border-transparent hover:text-gray-600 transition-colors focus:outline-none';
    document.getElementById('nav-dashboard').className = view === 'dashboard' ? activeNav : inactiveNav;
    document.getElementById('nav-settings').className = view === 'settings' ? activeNav : inactiveNav;
    document.getElementById('nav-logs').className = view === 'logs' ? activeNav : inactiveNav;

    if (view === 'settings') {
        fetchSites();
    } else if (view === 'logs') {
        fetchCrawlHistory();
    } else {
        fetchResults(currentProfile);
        fetchSiteStats();
    }
}

// ─── Dashboard ─────────────────────────────────────────────────
async function fetchResults(profile) {
    currentProfile = profile;

    const activeTab = 'h-full text-xs font-semibold text-gray-900 border-b-2 border-gray-900 transition-colors focus:outline-none';
    const inactiveTab = 'h-full text-xs font-medium text-gray-400 border-b-2 border-transparent hover:text-gray-600 transition-colors focus:outline-none';
    document.getElementById('tab-A').className = profile === 'A' ? activeTab : inactiveTab;
    document.getElementById('tab-B').className = profile === 'B' ? activeTab : inactiveTab;
    document.getElementById('tab-AI').className = profile === 'AI' ? activeTab : inactiveTab;

    const listContainer = document.getElementById('results-list');
    const loading = document.getElementById('loading');
    listContainer.innerHTML = '';
    loading.classList.remove('hidden');

    try {
        const url = profile === 'AI' ? `${API_BASE}/results/ai` : `${API_BASE}/results?profile=${profile}`;
        const res = await fetch(url);
        const data = await res.json();
        loading.classList.add('hidden');
        allResults = data;
        currentCompany = null;
        renderCompanyFilter(data, profile);
        renderCards(data, profile);
    } catch (e) {
        loading.classList.add('hidden');
        showToast('결과를 불러오는 중 오류가 발생했습니다.', true);
    }
}

async function fetchSiteStats() {
    const container = document.getElementById('site-summary');
    if (!container) return;
    try {
        const res = await fetch(`${API_BASE}/stats/sites`);
        const data = await res.json();
        renderSiteStats(data);
    } catch (e) {
        console.error('Failed to fetch site stats', e);
    }
}

function renderCompanyFilter(data, profile) {
    const bar = document.getElementById('company-filter-bar');
    const btns = document.getElementById('company-filter-btns');
    if (!bar || !btns) return;

    // 회사별 건수 집계
    const counts = {};
    data.forEach(item => {
        counts[item.company] = (counts[item.company] || 0) + 1;
    });
    const companies = Object.entries(counts).sort((a, b) => b[1] - a[1]);

    if (companies.length === 0) {
        bar.classList.add('hidden');
        return;
    }

    bar.classList.remove('hidden');
    btns.innerHTML = '';

    const accentColor = profile === 'A' ? 'bg-pink-500 text-white' : profile === 'AI' ? 'bg-violet-600 text-white' : 'bg-blue-600 text-white';

    companies.forEach(([company, count]) => {
        btns.innerHTML += `
        <button onclick="filterByCompany('${company.replace(/'/g, "\\'")}')"
            id="filter-${CSS.escape(company)}"
            class="company-filter-btn text-xs font-medium px-2.5 py-1 rounded-md bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors">
            ${company} <span class="text-gray-400 font-normal">${count}</span>
        </button>`;
    });

    // 전체 버튼 색상 보정 (profile에 따라)
    document.getElementById('filter-all').className =
        `text-xs font-medium px-2.5 py-1 rounded-md ${accentColor} transition-colors`;
}

function filterByCompany(company) {
    currentCompany = company;

    // 전체 버튼 스타일
    const profile = currentProfile;
    const accentColor = profile === 'A' ? 'bg-pink-500 text-white' : profile === 'AI' ? 'bg-violet-600 text-white' : 'bg-blue-600 text-white';
    const allBtn = document.getElementById('filter-all');
    allBtn.className = `text-xs font-medium px-2.5 py-1 rounded-md ${company === null ? accentColor : 'bg-gray-100 text-gray-600 hover:bg-gray-200'} transition-colors`;

    // 회사 버튼 스타일
    document.querySelectorAll('.company-filter-btn').forEach(btn => {
        const isActive = btn.textContent.trim().startsWith(company || '');
        // onclick 속성에서 회사명 추출해서 비교
        const btnCompany = btn.getAttribute('onclick')?.match(/filterByCompany\('(.+?)'\)/)?.[1];
        btn.className = `company-filter-btn text-xs font-medium px-2.5 py-1 rounded-md transition-colors ${
            btnCompany === company ? accentColor : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        }`;
    });

    const filtered = company ? allResults.filter(item => item.company === company) : allResults;
    renderCards(filtered, profile);
}

function renderSiteStats(data) {
    const html = data.map(site => {
        const dotColor = site.status === 'active' ? 'bg-green-500' : 'bg-red-400';
        return `
        <div class="flex items-center gap-1.5 text-xs text-gray-500 cursor-default select-none">
            <span class="w-1.5 h-1.5 rounded-full ${dotColor} flex-shrink-0"></span>
            <span>${site.name}</span>
            <span class="font-semibold text-gray-900">${site.job_count}</span>
        </div>`;
    }).join('');

    const desktop = document.getElementById('site-summary');
    const mobile = document.getElementById('site-summary-mobile');
    if (desktop) desktop.innerHTML = html;
    if (mobile) mobile.innerHTML = html;
}

function toggleSiteStats() {
    const panel = document.getElementById('site-stats-panel');
    const chevron = document.getElementById('stats-chevron');
    const isHidden = panel.classList.contains('hidden');
    panel.classList.toggle('hidden', !isHidden);
    chevron.style.transform = isHidden ? 'rotate(180deg)' : '';
}

function renderCards(data, profile) {
    const listContainer = document.getElementById('results-list');
    listContainer.innerHTML = '';

    if (data.length === 0) {
        listContainer.innerHTML = `
        <div class="text-center py-16 px-6">
            <i class="fa-solid fa-folder-open text-2xl text-gray-200 mb-3 block"></i>
            <p class="text-sm text-gray-400">조건에 맞는 채용공고가 없습니다</p>
            <p class="text-xs text-gray-300 mt-1">크롤링 버튼을 눌러 새로 수집해보세요</p>
        </div>`;
        return;
    }

    data.forEach(item => {
        const keywords = item.matched_keywords
            ? item.matched_keywords.split(',').map(k => k.trim()).filter(Boolean)
            : [];
        const keywordText = keywords.slice(0, 5).join(' · ');
        const moreCount = keywords.length > 5 ? ` +${keywords.length - 5}` : '';
        const deadline = item.deadline || '상시';

        listContainer.innerHTML += `
        <div class="px-5 py-4 border-b border-gray-50 last:border-b-0 hover:bg-gray-50 transition-colors">
            <div class="flex items-center gap-2 mb-1">
                <span class="text-xs font-medium text-gray-400">${item.company}</span>
            </div>
            <h3 class="text-sm font-semibold text-gray-900 truncate mb-1.5" title="${item.title}">
                <a href="${item.url}" target="_blank" class="hover:text-blue-600 transition-colors">${item.title}</a>
            </h3>
            <div class="flex items-center justify-between gap-4">
                <span class="text-xs text-gray-400 truncate">${keywordText}${moreCount}</span>
                <span class="text-xs text-gray-400 whitespace-nowrap shrink-0">${deadline}</span>
            </div>
        </div>`;
    });
}

async function triggerCrawl() {
    const btn = document.getElementById('btn-crawl');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin text-xs"></i>수집 중...';
    btn.disabled = true;
    btn.classList.add('opacity-70', 'cursor-not-allowed');

    try {
        const res = await fetch(`${API_BASE}/crawl`, { method: 'POST' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const msg = `완료 — A ${data.details.matched_summary.A}건, B ${data.details.matched_summary.B}건 매칭`;
        showToast(msg);
        fetchResults(currentProfile);
        fetchSiteStats();
    } catch (e) {
        showToast('크롤링 중 오류가 발생했습니다.', true);
    } finally {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
        btn.classList.remove('opacity-70', 'cursor-not-allowed');
    }
}

async function exportHtml() {
    try {
        const res = await fetch(`${API_BASE}/export`, { method: 'POST' });
        const data = await res.json();
        showToast(`보고서 저장: ${data.file_path}`);
    } catch (e) {
        showToast('내보내기 실패', true);
    }
}

async function deleteSite(siteId, siteName) {
    if (!confirm(`"${siteName}" 사이트와 관련 데이터를 모두 삭제합니다.`)) return;
    try {
        const res = await fetch(`${API_BASE}/sites/${siteId}`, { method: 'DELETE' });
        if (!res.ok) throw new Error();
        showToast(`"${siteName}" 삭제 완료`);
        fetchSites();
        fetchSiteStats();
    } catch (e) {
        showToast('삭제 중 오류가 발생했습니다.', true);
    }
}

// ─── Settings ──────────────────────────────────────────────────
async function fetchSites() {
    const container = document.getElementById('sites-list');
    container.innerHTML = '<div class="px-5 py-8 text-center text-xs text-gray-400">불러오는 중...</div>';

    try {
        const res = await fetch(`${API_BASE}/sites`);
        const data = await res.json();

        if (!data.length) {
            container.innerHTML = '<div class="px-5 py-10 text-center text-xs text-gray-400">등록된 사이트가 없습니다</div>';
            return;
        }

        container.innerHTML = '';
        data.forEach(site => {
            const isActive = site.status === 'active';
            const isError = site.status === 'parse_error';
            const dotColor = isActive ? 'bg-green-500' : isError ? 'bg-red-400' : 'bg-gray-300';
            const statusText = isActive ? '정상' : isError ? '오류' : site.status;
            const statusColor = isActive ? 'text-green-600' : isError ? 'text-red-500' : 'text-gray-400';

            container.innerHTML += `
            <div class="flex items-center gap-3 px-5 py-3.5 border-b border-gray-50 last:border-b-0 hover:bg-gray-50/50 transition-colors">
                <span class="w-1.5 h-1.5 rounded-full ${dotColor} flex-shrink-0"></span>
                <div class="flex-1 min-w-0">
                    <div class="text-sm font-medium text-gray-800 truncate">${site.name}</div>
                    <a href="${site.url}" target="_blank" class="text-xs text-gray-400 hover:text-blue-500 transition-colors truncate block">${site.url}</a>
                </div>
                <span class="text-xs ${statusColor} whitespace-nowrap">${statusText}</span>
                <button onclick="deleteSite(${site.id}, '${site.name.replace(/'/g, "\\'")}')"
                    class="text-gray-300 hover:text-red-400 transition-colors ml-1 flex-shrink-0" title="삭제">
                    <i class="fa-solid fa-trash text-xs"></i>
                </button>
            </div>`;
        });
    } catch (e) {
        container.innerHTML = '<div class="px-5 py-8 text-center text-xs text-red-400">로딩 오류</div>';
    }
}

document.getElementById('site-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.textContent = '추가 중...';

    try {
        await fetch(`${API_BASE}/sites`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: document.getElementById('site-name').value,
                url: document.getElementById('site-url').value,
            }),
        });
        showToast('사이트가 추가되었습니다.');
        document.getElementById('site-form').reset();
        fetchSites();
    } catch (err) {
        showToast('추가 중 오류가 발생했습니다.', true);
    } finally {
        btn.disabled = false;
        btn.textContent = '추가';
    }
});

// ─── Toast ─────────────────────────────────────────────────────
let toastTimeout;
function showToast(message, isError = false) {
    const toast = document.getElementById('toast');
    const msgEl = document.getElementById('toast-message');
    const icon = toast.querySelector('i');

    msgEl.textContent = message;

    if (isError) {
        toast.className = 'fixed bottom-5 right-5 transform transition-all duration-200 translate-y-0 opacity-100 bg-red-600 text-white text-xs px-4 py-2.5 rounded-lg shadow-lg flex items-center gap-2 z-50';
        icon.className = 'fa-solid fa-triangle-exclamation text-xs';
    } else {
        toast.className = 'fixed bottom-5 right-5 transform transition-all duration-200 translate-y-0 opacity-100 bg-gray-900 text-white text-xs px-4 py-2.5 rounded-lg shadow-lg flex items-center gap-2 z-50';
        icon.className = 'fa-solid fa-circle-check text-green-400 text-xs';
    }

    clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => {
        toast.classList.remove('translate-y-0', 'opacity-100');
        toast.classList.add('translate-y-4', 'opacity-0');
    }, 4000);
}

// ─── Crawl History (Logs) ──────────────────────────────────────
async function fetchCrawlHistory() {
    const container = document.getElementById('crawl-history');
    container.innerHTML = '<div class="text-center py-10 text-xs text-gray-400">불러오는 중...</div>';
    try {
        const res = await fetch(`${API_BASE}/crawl/history`);
        const data = await res.json();
        renderCrawlHistory(data);
    } catch (e) {
        container.innerHTML = '<div class="text-center py-10 text-xs text-red-400">로딩 오류</div>';
    }
}

function formatDuration(sec) {
    if (sec == null) return '';
    if (sec < 60) return `${sec}초`;
    return `${Math.floor(sec / 60)}분 ${sec % 60}초`;
}

function formatDatetime(iso) {
    if (!iso) return '-';
    const d = new Date(iso);
    const pad = n => String(n).padStart(2, '0');
    return `${d.getFullYear()}.${pad(d.getMonth()+1)}.${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function renderCrawlHistory(data) {
    const container = document.getElementById('crawl-history');
    if (!data.length) {
        container.innerHTML = `
        <div class="text-center py-16 px-6">
            <i class="fa-solid fa-clock-rotate-left text-2xl text-gray-200 mb-3 block"></i>
            <p class="text-sm text-gray-400">크롤링 이력이 없습니다</p>
            <p class="text-xs text-gray-300 mt-1">크롤링을 실행하면 여기에 기록됩니다</p>
        </div>`;
        return;
    }

    container.innerHTML = data.map(s => {
        const siteRows = (s.site_results || []).map(r => {
            const dot = r.status === 'success' ? 'bg-green-500' : 'bg-red-400';
            const jobText = r.jobs_found > 0 ? `<span class="font-medium text-gray-700">+${r.jobs_found}건</span>` : '<span class="text-gray-300">0건</span>';
            const errText = r.error ? `<span class="text-red-400 truncate ml-2" title="${r.error}">${r.error}</span>` : '';
            return `<div class="flex items-center gap-2 py-1 text-xs text-gray-500">
                <span class="w-1.5 h-1.5 rounded-full ${dot} flex-shrink-0 ml-1"></span>
                <span class="w-24 truncate">${r.name}</span>
                ${jobText}
                ${errText}
            </div>`;
        }).join('');

        const failedBadge = s.failed > 0
            ? `<span class="text-red-500">${s.failed}실패</span>`
            : `<span class="text-gray-400">${s.failed}실패</span>`;

        return `
        <div class="bg-white border border-gray-100 rounded-lg overflow-hidden">
            <button onclick="toggleSessionDetail(${s.id})"
                class="w-full px-5 py-3.5 flex items-center gap-3 hover:bg-gray-50 transition-colors text-left">
                <i id="chevron-${s.id}" class="fa-solid fa-chevron-right text-xs text-gray-300 transition-transform duration-200 flex-shrink-0"></i>
                <div class="flex-1 min-w-0 flex flex-wrap items-center gap-x-4 gap-y-1">
                    <span class="text-xs font-medium text-gray-700 whitespace-nowrap">${formatDatetime(s.started_at)}</span>
                    <span class="text-xs text-gray-400">${s.total_sites}사이트</span>
                    <span class="text-xs text-green-600">${s.success}성공</span>
                    ${failedBadge}
                    <span class="text-xs font-semibold text-gray-800">+${s.new_jobs}건</span>
                    <span class="text-xs text-gray-400">A:${s.matched_a} B:${s.matched_b}</span>
                    ${s.duration_sec != null ? `<span class="text-xs text-gray-300">${formatDuration(s.duration_sec)}</span>` : ''}
                </div>
            </button>
            <div id="detail-${s.id}" class="hidden border-t border-gray-50 px-5 py-2">
                ${siteRows}
            </div>
        </div>`;
    }).join('');
}

function toggleSessionDetail(id) {
    const detail = document.getElementById(`detail-${id}`);
    const chevron = document.getElementById(`chevron-${id}`);
    const isHidden = detail.classList.contains('hidden');
    detail.classList.toggle('hidden', !isHidden);
    chevron.style.transform = isHidden ? 'rotate(90deg)' : '';
}

// ─── Init ───────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    fetchResults('A');
    fetchSiteStats();
});
