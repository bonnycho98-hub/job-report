// Kakao SDK Initialization Placeholder
// 사용자가 발급받은 JS Key로 교체해야 합니다. 
const KAKAO_JS_KEY = 'YOUR_KAKAO_JS_KEY_HERE'; 
if (KAKAO_JS_KEY !== 'YOUR_KAKAO_JS_KEY_HERE') {
    Kakao.init(KAKAO_JS_KEY);
    console.log('Kakao SDK Initialized:', Kakao.isInitialized());
}

// State Management
let currentProfile = 'A';
let appState = {
    jobs: [],
    stats: null,
    trend: null
};

// DOM Elements
const views = {
    list: document.getElementById('view-list'),
    analysis: document.getElementById('view-analysis'),
    matching: document.getElementById('view-matching')
};

const tabs = document.querySelectorAll('.tab, .nav-item');

// Tab Navigation
tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        const targetView = tab.getAttribute('data-tab');
        if (!targetView) return;
        switchTab(targetView);
    });
});

function switchTab(viewId) {
    // Hide all views
    Object.values(views).forEach(v => v.style.display = 'none');
    // Show target view
    views[viewId].style.display = 'block';
    
    // Update active tab styles
    document.querySelectorAll('.tab, .nav-item').forEach(t => {
        if (t.getAttribute('data-tab') === viewId) {
            t.classList.add('active');
        } else {
            t.classList.remove('active');
        }
    });

    if (viewId === 'analysis') loadAnalysis();
    if (viewId === 'matching') loadMatching(currentProfile);
}

// Data Fetching
async function fetchJobs() {
    const jobListEl = document.getElementById('job-list');
    try {
        const response = await fetch('/api/results?profile=A'); // Default for list
        const data = await response.json();
        appState.jobs = data;
        renderJobs(data, jobListEl);
        document.getElementById('job-count').textContent = data.length;
    } catch (error) {
        console.error('Fetch Jobs Error:', error);
        jobListEl.innerHTML = '<p style="padding: 20px; text-align: center; color: var(--text-mute);">데이터를 불러오지 못했습니다.</p>';
    }
}

function renderJobs(jobs, container) {
    container.innerHTML = '';
    if (jobs.length === 0) {
        container.innerHTML = '<div class="card"><p style="text-align:center; color:var(--text-mute);">등록된 공고가 없습니다.</p></div>';
        return;
    }

    jobs.forEach(job => {
        const item = document.createElement('div');
        item.className = 'card';
        item.style.padding = '16px';
        item.innerHTML = `
            <div class="job-item">
                <div class="job-icon">
                    <i class="fa-solid fa-building"></i>
                </div>
                <div class="job-info">
                    <div class="job-company">${job.company}</div>
                    <div class="job-title">${job.title}</div>
                    <div class="job-meta">
                        <span><i class="fa-solid fa-user-tag"></i> ${job.position || 'N/A'}</span>
                        <span><i class="fa-solid fa-star"></i> ${job.score}점</span>
                    </div>
                </div>
                <div class="job-actions">
                   <button onclick="shareToKakao('${job.title}', '${job.company}', '${job.url}')" style="background:none; border:none; font-size: 20px; color: #fee500; cursor:pointer;">
                       <i class="fa-solid fa-comment"></i>
                   </button>
                </div>
            </div>
            <div style="margin-top: 12px; display: flex; justify-content: flex-end;">
                 <a href="${job.url}" target="_blank" class="badge badge-primary" style="text-decoration:none;">공고 보기 <i class="fa-solid fa-chevron-right"></i></a>
            </div>
        `;
        container.appendChild(item);
    });
}

// Analysis View Logic
async function loadAnalysis() {
    try {
        const response = await fetch('/api/stats/sites');
        const stats = await response.json();
        renderSiteChart(stats);
        renderTrendChart();
    } catch (error) {
        console.error('Analysis Load Error:', error);
    }
}

function renderSiteChart(data) {
    const ctx = document.getElementById('siteChart').getContext('2d');
    if (window.mySiteChart) window.mySiteChart.destroy();

    window.mySiteChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.name),
            datasets: [{
                data: data.map(d => d.job_count),
                backgroundColor: ['#3182f6', '#00d084', '#ff8e0d', '#abb8c3', '#eb144c'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { usePointStyle: true, padding: 20 } }
            },
            cutout: '70%'
        }
    });
}

function renderTrendChart() {
    const ctx = document.getElementById('trendChart').getContext('2d');
    if (window.myTrendChart) window.myTrendChart.destroy();

    // Mock trend data (Wait for backend support if needed)
    window.myTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['4주 전', '3주 전', '2주 전', '이번 주'],
            datasets: [{
                label: '수집 공고',
                data: [45, 52, 38, 65],
                borderColor: '#3182f6',
                tension: 0.4,
                fill: true,
                backgroundColor: 'rgba(49, 130, 246, 0.1)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { display: false }, x: { grid: { display: false } } }
        }
    });
}

// Matching View Logic
async function loadMatching(profile) {
    currentProfile = profile;
    const matchingListEl = document.getElementById('matching-list');
    matchingListEl.innerHTML = '<div class="card skeleton" style="height: 100px;"></div>'.repeat(3);
    
    // UI Feedback for profile buttons
    const btnA = document.getElementById('btn-profile-A');
    const btnB = document.getElementById('btn-profile-B');
    if (profile === 'A') {
        btnA.style.background = 'white'; btnA.style.color = '#3182f6';
        btnB.style.background = 'rgba(255,255,255,0.2)'; btnB.style.color = 'white';
    } else {
        btnB.style.background = 'white'; btnB.style.color = '#3182f6';
        btnA.style.background = 'rgba(255,255,255,0.2)'; btnA.style.color = 'white';
    }

    try {
        const response = await fetch(`/api/results?profile=${profile}`);
        const data = await response.json();
        renderJobs(data, matchingListEl);
    } catch (error) {
        console.error('Matching Load Error:', error);
    }
}

// KakaoTalk Sharing
function shareToKakao(title, company, url) {
    if (KAKAO_JS_KEY === 'YOUR_KAKAO_JS_KEY_HERE') {
        alert('카카오톡 공유 기능을 사용하려면 mobile.js 상단에 카카오 앱 키를 설정해야 합니다.');
        return;
    }

    Kakao.Share.sendDefault({
        objectType: 'feed',
        content: {
            title: `[공고 알림] ${company}`,
            description: `${title}\n당신에게 맞는 새로운 공고가 올라왔습니다.`,
            imageUrl: 'https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?auto=format&fit=crop&q=80&w=300&h=200', 
            link: {
                mobileWebUrl: url,
                webUrl: url,
            },
        },
        buttons: [
            {
                title: '공고 확인하기',
                link: {
                    mobileWebUrl: url,
                    webUrl: url,
                },
            },
        ],
    });
}

// Refresh Handler
document.getElementById('btn-refresh').addEventListener('click', async () => {
    const btn = document.getElementById('btn-refresh');
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 로딩중';
    await fetchJobs();
    btn.innerHTML = '<i class="fa-solid fa-rotate"></i> 갱신';
});

// Init
window.addEventListener('DOMContentLoaded', () => {
    fetchJobs();
});
