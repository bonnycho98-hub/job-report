const API_BASE = '/api';
let currentProfile = 'A';

// --- UI Navigation ---
function switchTab(view) {
    document.getElementById('view-dashboard').classList.toggle('hidden', view !== 'dashboard');
    document.getElementById('view-settings').classList.toggle('hidden', view !== 'settings');

    document.getElementById('nav-dashboard').className = view === 'dashboard'
        ? 'text-blue-600 font-semibold focus:outline-none' : 'text-gray-500 hover:text-gray-800 focus:outline-none';
    document.getElementById('nav-settings').className = view === 'settings'
        ? 'text-blue-600 font-semibold focus:outline-none' : 'text-gray-500 hover:text-gray-800 focus:outline-none';

    if (view === 'settings') {
        fetchSites();
    } else {
        fetchResults(currentProfile);
        fetchSiteStats();
    }
}

// --- Dashboard ---
async function fetchResults(profile) {
    currentProfile = profile;

    // Update Tab UI
    const tabA = document.getElementById('tab-A');
    const tabB = document.getElementById('tab-B');
    if (profile === 'A') {
        tabA.className = "px-6 py-2 rounded-t-lg bg-pink-50 text-pink-700 font-semibold border-b-2 border-pink-500 focus:outline-none transition-colors";
        tabB.className = "px-6 py-2 rounded-t-lg text-gray-500 hover:bg-gray-100 font-medium border-b-2 border-transparent focus:outline-none transition-colors";
    } else {
        tabB.className = "px-6 py-2 rounded-t-lg bg-blue-50 text-blue-700 font-semibold border-b-2 border-blue-500 focus:outline-none transition-colors";
        tabA.className = "px-6 py-2 rounded-t-lg text-gray-500 hover:bg-gray-100 font-medium border-b-2 border-transparent focus:outline-none transition-colors";
    }

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
        showToast("결과를 불러오는 중 오류가 발생했습니다.", true);
    }
}

async function fetchSiteStats() {
    const summaryContainer = document.getElementById('site-summary');
    if (!summaryContainer) return;

    try {
        const res = await fetch(`${API_BASE}/stats/sites`);
        const data = await res.json();
        renderSiteStats(data);
    } catch (e) {
        console.error("Failed to fetch site stats", e);
    }
}

function renderSiteStats(data) {
    const container = document.getElementById('site-summary');
    if (!container) return;
    container.innerHTML = '';

    data.forEach(site => {
        const dotColor = site.status === 'active' ? 'bg-green-500' : 'bg-red-500';
        container.innerHTML += `
        <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex flex-col items-center justify-center text-center hover:shadow-md transition-all relative overflow-hidden group">
            <div class="absolute top-2 right-2">
                <span class="flex h-2 w-2">
                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full ${dotColor} opacity-75"></span>
                    <span class="relative inline-flex rounded-full h-2 w-2 ${dotColor}"></span>
                </span>
            </div>
            <span class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1 group-hover:text-blue-500 transition-colors">${site.name}</span>
            <div class="flex items-baseline gap-1">
                <span class="text-2xl font-black text-gray-800 group-hover:text-blue-600 transition-colors">${site.job_count}</span>
                <span class="text-xs font-bold text-gray-400">건</span>
            </div>
        </div>
        `;
    });
}


function renderCards(data, profile) {
    const listContainer = document.getElementById('results-list');
    if (data.length === 0) {
        listContainer.innerHTML = `<div class="col-span-full text-center py-16 text-gray-500 bg-white rounded-xl shadow border border-dashed border-gray-300">
            <i class="fa-solid fa-folder-open text-5xl mb-4 text-gray-300"></i><br>
            <span class="font-medium text-lg">조건에 맞는 채용공고가 아직 없습니다.</span><br>우측 상단의 크롤링 버튼을 눌러 새로고침해보세요.
        </div>`;
        return;
    }

    const badgeColor = profile === 'A' ? 'bg-pink-100 text-pink-800 border-pink-200' : 'bg-blue-100 text-blue-800 border-blue-200';
    const topBarColor = profile === 'A' ? 'bg-pink-400' : 'bg-blue-500';

    data.forEach(item => {
        const keywords = item.matched_keywords ? item.matched_keywords.split(',') : [];
        const keywordTags = keywords.slice(0, 3).map(k => `<span class="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded shadow-sm border border-gray-200">${k}</span>`).join('');

        // 날짜 포맷
        const dateObj = new Date(item.crawled_at);
        const dateStr = `${dateObj.getMonth() + 1}/${dateObj.getDate()} ${dateObj.getHours()}:${String(dateObj.getMinutes()).padStart(2, '0')}`;

        const accentBorder = profile === 'A' ? 'border-l-pink-400' : 'border-l-blue-500';

        listContainer.innerHTML += `
        <div class="bg-white rounded-lg shadow hover:shadow-md transition-shadow duration-200 border-y border-r border-l-4 border-gray-100 ${accentBorder} p-5 flex flex-col md:flex-row md:items-center justify-between gap-6">
            
            <div class="flex-1 min-w-0">
                <div class="flex items-center gap-3 mb-2">
                    <span class="text-xs font-bold px-2.5 py-1 rounded border ${badgeColor}">${item.sub_group || 'Keyword Match'} (점수: ${item.score})</span>
                    <span class="text-sm text-gray-500 font-semibold">${item.company}</span>
                </div>
                <h3 class="text-xl font-extrabold text-gray-900 truncate" title="${item.title}">
                    <a href="${item.url}" target="_blank" class="hover:text-blue-600 transition-colors">${item.title}</a>
                </h3>
                <div class="text-sm text-gray-600 truncate mt-1.5 flex items-center">
                    <i class="fa-solid fa-briefcase mr-2 text-gray-400"></i> ${item.position}
                </div>
            </div>

            <div class="flex flex-col md:items-end justify-center min-w-[240px]">
                <div class="flex flex-wrap gap-1.5 mb-3 justify-start md:justify-end">
                    ${keywordTags}
                    ${keywords.length > 3 ? `<span class="text-xs text-gray-400 font-medium px-1 flex items-center">+${keywords.length - 3}</span>` : ''}
                </div>
                <div class="flex items-center gap-4 text-sm font-medium">
                    <span class="text-gray-400 flex items-center" title="수집 시간">
                        <i class="fa-solid fa-clock mr-1.5 text-gray-300"></i> ${dateStr}
                    </span>
                    <span class="text-red-500 bg-red-50 px-2.5 py-1 rounded border border-red-100 whitespace-nowrap">${item.deadline ? item.deadline : '상시/미정'}</span>
                </div>
            </div>
            
        </div>
        `;
    });
}

async function triggerCrawl() {
    const btn = document.getElementById('btn-crawl');
    const originalContent = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin mr-2"></i>수집 및 매칭 중...';
    btn.disabled = true;
    btn.classList.add('opacity-80', 'cursor-not-allowed');

    try {
        const res = await fetch(`${API_BASE}/crawl`, { method: 'POST' });
        if (!res.ok) throw new Error(`서버 응답 오류 (HTTP ${res.status})`);
        const data = await res.json();
        const msg = `크롤링 완료! 새로 매칭된 공고: A ${data.details.matched_summary.A}건, B ${data.details.matched_summary.B}건`;
        showToast(msg);
        fetchResults(currentProfile);
        fetchSiteStats();
    } catch (e) {
        showToast("크롤링 실행 중 네트워크 오류가 발생했습니다.", true);
    } finally {
        btn.innerHTML = originalContent;
        btn.disabled = false;
        btn.classList.remove('opacity-80', 'cursor-not-allowed');
    }
}

async function exportHtml() {
    try {
        const res = await fetch(`${API_BASE}/export`, { method: 'POST' });
        const data = await res.json();
        showToast(`보고서 저장 완료: ${data.file_path}`);
    } catch (e) {
        showToast("내보내기 실패했습니다.", true);
    }
}

// --- Settings ---
async function fetchSites() {
    const tbody = document.getElementById('sites-table-body');
    tbody.innerHTML = '<tr><td colspan="4" class="text-center py-6 border border-dashed border-gray-200 text-gray-500 rounded-lg">데이터 불어오는 중...</td></tr>';

    try {
        const res = await fetch(`${API_BASE}/sites`);
        const data = await res.json();

        tbody.innerHTML = data.length ? '' : '<tr><td colspan="4" class="text-center py-8 text-gray-500 bg-gray-50">등록된 사이트가 아직 없습니다.</td></tr>';

        data.forEach(site => {
            const statusColor = site.status === 'active' ? 'bg-green-100 text-green-800 border-green-200' :
                (site.status === 'parse_error' ? 'bg-red-100 text-red-800 border-red-200' : 'bg-gray-100 text-gray-800 border-gray-200');
            tbody.innerHTML += `
            <tr class="hover:bg-blue-50 transition-colors">
                <td class="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-semibold text-gray-700">${site.id}</td>
                <td class="whitespace-nowrap px-3 py-4 text-sm font-medium text-gray-900">${site.name}</td>
                <td class="px-3 py-4 text-sm text-gray-500 max-w-xs truncate" title="${site.url}">
                    <a href="${site.url}" target="_blank" class="hover:text-blue-600 underline decoration-blue-300 underline-offset-2">${site.url}</a>
                </td>
                <td class="whitespace-nowrap px-3 py-4 text-sm">
                    <span class="inline-flex items-center rounded-md px-2.5 py-1 text-xs font-bold border ${statusColor} shadow-sm">
                        ${site.status === 'active' ? '<i class="fa-solid fa-circle-check mr-1"></i>정상' :
                    (site.status === 'parse_error' ? '<i class="fa-solid fa-circle-xmark mr-1"></i>오류' : site.status)}
                    </span>
                </td>
            </tr>
            `;
        });
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center py-8 text-red-500 bg-red-50">데이터 로딩 에러</td></tr>';
    }
}

document.getElementById('site-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    btn.disabled = true;
    btn.innerHTML = '추가 중...';

    const siteData = {
        name: document.getElementById('site-name').value,
        url: document.getElementById('site-url').value
    };

    try {
        await fetch(`${API_BASE}/sites`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(siteData)
        });
        showToast("사이트가 성공적으로 추가되었습니다.");
        document.getElementById('site-form').reset();
        fetchSites();
    } catch (error) {
        showToast("추가 중 오류가 발생했습니다.", true);
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'URL 추가';
    }
});

// --- Utils ---
let toastTimeout;
function showToast(message, isError = false) {
    const toast = document.getElementById('toast');
    const msgEl = document.getElementById('toast-message');
    const icon = toast.querySelector('i');

    msgEl.textContent = message;

    if (isError) {
        toast.className = 'fixed bottom-5 right-5 transform transition-all duration-300 translate-y-0 opacity-100 bg-red-600 text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50 ring-4 ring-red-400 ring-opacity-30';
        icon.className = 'fa-solid fa-triangle-exclamation text-white text-xl';
    } else {
        toast.className = 'fixed bottom-5 right-5 transform transition-all duration-300 translate-y-0 opacity-100 bg-gray-800 text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50 ring-4 ring-gray-900 ring-opacity-20';
        icon.className = 'fa-solid fa-circle-check text-green-400 text-xl';
    }

    clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => {
        toast.classList.remove('translate-y-0', 'opacity-100');
        toast.classList.add('translate-y-20', 'opacity-0');
    }, 4000);
}

// Initial load
document.addEventListener('DOMContentLoaded', () => {
    fetchResults('A');
    fetchSiteStats();
});
