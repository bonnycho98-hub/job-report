const API_BASE = '/api';
let currentProfile = 'A';

// ─── Navigation ────────────────────────────────────────────────
function switchTab(view) {
    document.getElementById('view-dashboard').classList.toggle('hidden', view !== 'dashboard');
    document.getElementById('view-settings').classList.toggle('hidden', view !== 'settings');

    const activeNav = 'h-full px-3 text-xs font-medium text-gray-900 border-b-2 border-gray-900 transition-colors focus:outline-none';
    const inactiveNav = 'h-full px-3 text-xs font-medium text-gray-400 border-b-2 border-transparent hover:text-gray-600 transition-colors focus:outline-none';
    document.getElementById('nav-dashboard').className = view === 'dashboard' ? activeNav : inactiveNav;
    document.getElementById('nav-settings').className = view === 'settings' ? activeNav : inactiveNav;

    if (view === 'settings') {
        fetchSites();
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

    const listContainer = document.getElementById('results-list');
    const loading = document.getElementById('loading');
    listContainer.innerHTML = '';
    loading.classList.remove('hidden');

    try {
        const res = await fetch(`${API_BASE}/results?profile=${profile}`);
        const data = await res.json();
        loading.classList.add('hidden');
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

function renderSiteStats(data) {
    const container = document.getElementById('site-summary');
    if (!container) return;
    container.innerHTML = '';

    data.forEach(site => {
        const dotColor = site.status === 'active' ? 'bg-green-500' : 'bg-red-400';
        container.innerHTML += `
        <div class="flex items-center gap-1.5 text-xs text-gray-500 cursor-default select-none">
            <span class="w-1.5 h-1.5 rounded-full ${dotColor} flex-shrink-0"></span>
            <span>${site.name}</span>
            <span class="font-semibold text-gray-900">${site.job_count}</span>
        </div>`;
    });
}

function renderCards(data, profile) {
    const listContainer = document.getElementById('results-list');

    if (data.length === 0) {
        listContainer.innerHTML = `
        <div class="text-center py-16 px-6">
            <i class="fa-solid fa-folder-open text-2xl text-gray-200 mb-3 block"></i>
            <p class="text-sm text-gray-400">조건에 맞는 채용공고가 없습니다</p>
            <p class="text-xs text-gray-300 mt-1">크롤링 버튼을 눌러 새로 수집해보세요</p>
        </div>`;
        return;
    }

    const badgeColor = profile === 'A'
        ? 'bg-pink-50 text-pink-600 border-pink-100'
        : 'bg-blue-50 text-blue-600 border-blue-100';

    data.forEach(item => {
        const keywords = item.matched_keywords
            ? item.matched_keywords.split(',').map(k => k.trim()).filter(Boolean)
            : [];
        const keywordText = keywords.slice(0, 5).join(' · ');
        const moreCount = keywords.length > 5 ? ` +${keywords.length - 5}` : '';
        const deadline = item.deadline || '상시';

        listContainer.innerHTML += `
        <div class="px-5 py-4 border-b border-gray-50 last:border-b-0 hover:bg-gray-50/60 transition-colors">
            <div class="flex items-center gap-2 mb-1">
                <span class="text-xs font-medium text-gray-400">${item.company}</span>
                <span class="text-[10px] px-1.5 py-0.5 rounded border ${badgeColor} leading-tight">${item.sub_group || 'Match'}</span>
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
    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin text-[10px]"></i>수집 중...';
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

// ─── Init ───────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    fetchResults('A');
    fetchSiteStats();
});
