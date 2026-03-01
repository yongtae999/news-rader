// 전역 뉴스 데이터 변수
let newsData = { hunting: [], asf: [], ai: [], ecosystem: [], association: [], editorial: [] };

// --- 날짜 표시 영역 ---
// 날짜 포맷 함수 (YY.MM.DD)
function formatDate(date) {
    const year = date.getFullYear().toString().slice(2);
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}.${month}.${day}`;
}

// 상단 헤더 오늘 날짜 설정
function displayDate() {
    const today = new Date();
    const dateElement = document.getElementById('currentDate');
    const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'short' };
    const dateString = today.toLocaleDateString('ko-KR', options);

    dateElement.innerHTML = `<i class="fa-regular fa-calendar-check"></i> ${dateString}`;
}

// '몇 일 전'을 기반으로 최근 날짜를 계산해주는 함수 (매일 업데이트 시뮬레이션 용도)
function calculatePublishedDate(daysAgo) {
    const today = new Date();
    today.setDate(today.getDate() - daysAgo);
    return formatDate(today);
}

// 뉴스 카드 HTML 생성 함수
function createNewsCard(newsItem, index) {
    const imageUrl = newsItem.image;
    let categoryName = '';

    switch (currentCategory) {
        case 'hunting': categoryName = "수렵관련"; break;
        case 'asf': categoryName = "ASF관련"; break;
        case 'ai': categoryName = "AI관련"; break;
        case 'ecosystem': categoryName = "교란생물 관련"; break;
        case 'association': categoryName = "협회 관련"; break;
        case 'editorial': categoryName = "사설/기획"; break;
    }

    // 서버에서 전달한 실제 발행일(date)을 최우선으로 사용하고 없으면 기존 로직 폴백
    const publishedDate = newsItem.date || calculatePublishedDate(newsItem.daysAgo);
    let isNew = newsItem.daysAgo === 0 ? '<span style="color:var(--accent-color); font-weight:bold; margin-right: 5px;">[새소식]</span>' : '';

    return `
        <a href="#" class="news-card" aria-label="${newsItem.title} 기사 읽기" onclick="openNewsModal(${newsItem.id}); return false;">
            <div class="card-content">
                <div class="card-meta">
                    <span class="card-category-badge">${categoryName}</span>
                <span class="card-source"><i class="fa-regular fa-building"></i> ${newsItem.source}</span>
                <span class="card-date"><i class="fa-regular fa-clock"></i> ${publishedDate}</span>
            </div>
            <h2 class="card-title">${isNew}${newsItem.title}</h2>
            <p class="card-excerpt">${newsItem.excerpt}</p>
            <div class="card-footer">
                <span>자세히 보기</span>
                <i class="fa-solid fa-arrow-right"></i>
            </div>
        </div>
    </a>
    `;
}

// 렌더링 관련 전역 변수
let currentCategory = 'hunting';
const newsListContainer = document.getElementById('newsList');
const loadingSpinner = document.getElementById('loadingSpinner');

// 뉴스 렌더링 로직
function renderNews(category) {
    // 이전 뉴스 페이드 아웃
    newsListContainer.classList.add('fade-out');
    loadingSpinner.classList.add('active');

    setTimeout(() => {
        const items = newsData[category];

        if (items && items.length > 0) {
            // 날짜 최신순 정렬 (daysAgo 기준 오름차순 - 0이 제일 최신)
            const sortedItems = [...items].sort((a, b) => a.daysAgo - b.daysAgo);

            const html = sortedItems.map((item, index) => createNewsCard(item, index)).join('');
            newsListContainer.innerHTML = html;
        } else {
            newsListContainer.innerHTML = `
        < div class="empty-state" >
                    <i class="fa-regular fa-folder-open" style="font-size: 3rem; margin-bottom: 1rem; color: var(--text-secondary);"></i>
                    <p>현재 등록된 뉴스가 없습니다.</p>
                </div >
        `;
        }

        // 새로 렌더링된 요소 페이드 인
        loadingSpinner.classList.remove('active');
        newsListContainer.classList.remove('fade-out');
    }, 400); // 부드러운 전환을 위한 인위적 지연 (로딩 시뮬레이션)
}

// 탭 전환 핸들러
function initTabs() {
    const tabs = document.querySelectorAll('.tab-button');
    const indicator = document.querySelector('.tab-indicator');

    tabs.forEach((tab, index) => {
        tab.addEventListener('click', () => {
            // 이미 활성화된 탭이면 무시
            if (tab.classList.contains('active')) return;

            // 모든 탭 활성화 해제
            tabs.forEach(t => t.classList.remove('active'));

            // 클릭된 탭 활성화
            tab.classList.add('active');

            // 데스크탑 인디케이터 슬라이딩 애니메이션 계산
            if (window.innerWidth > 768) {
                indicator.style.transform = `translateX(calc(${index * 100}% + ${index * 1}rem))`;
            }

            // 데이터 변경 렌더링 호출
            currentCategory = tab.getAttribute('data-category');
            renderNews(currentCategory);
        });
    });

    // 리사이즈 시 인디케이터 초기화 (모바일 <-> 해상도 전환 대비)
    window.addEventListener('resize', () => {
        if (window.innerWidth <= 768) {
            indicator.style.transform = 'none';
        } else {
            const activeIndex = Array.from(tabs).findIndex(t => t.classList.contains('active'));
            if (activeIndex !== -1) {
                indicator.style.transform = `translateX(calc(${activeIndex * 100}% + ${activeIndex * 1}rem))`;
            }
        }
    });
}

// 모달 동작 스크립트 추가
const modalOverlay = document.getElementById('newsModal');
const closeModalBtn = document.getElementById('closeModal');

function openNewsModal(newsId) {
    // 1. 해당 id의 기사 객체 찾기
    let targetNews = null;
    let targetCategoryName = '';

    // 이중 루프 대신 카테고리별로 순회하여 찾기
    for (const [key, items] of Object.entries(newsData)) {
        const found = items.find(item => item.id === newsId);
        if (found) {
            targetNews = found;
            if (key === 'hunting') targetCategoryName = '수렵관련';
            if (key === 'asf') targetCategoryName = 'ASF관련';
            if (key === 'ai') targetCategoryName = 'AI관련';
            if (key === 'ecosystem') targetCategoryName = '교란생물 관련';
            if (key === 'association') targetCategoryName = '협회 관련';
            if (key === 'editorial') targetCategoryName = '사설/기획';
            break;
        }
    }

    if (!targetNews) return;

    // 2. 모달 내 DOM 엘리먼트에 데이터 주입
    document.getElementById('modalCategory').textContent = targetCategoryName;
    document.getElementById('modalTitle').textContent = targetNews.title;
    document.getElementById('modalSource').innerHTML = `< i class="fa-regular fa-building" ></i > ${targetNews.source} `;

    const publishedDate = targetNews.date || calculatePublishedDate(targetNews.daysAgo);
    document.getElementById('modalDate').innerHTML = `<i class="fa-regular fa-clock"></i> ${publishedDate}`;

    // 본문 내용 생성 (항목별 실제 저장된 상세 body 텍스트 활용)
    const articleBodyHTML = `
        < p > <strong>${targetNews.excerpt}</strong></p >
            <p>${targetNews.body}</p>
    `;
    document.getElementById('modalBody').innerHTML = articleBodyHTML;

    // 3. 모달 열기 애니메이션 클래스 추가 및 배경 스크롤락
    modalOverlay.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeNewsModal() {
    modalOverlay.classList.remove('active');
    document.body.style.overflow = '';
}

// 주간 AI 브리핑 모달 열기 함수
async function openAIBriefingModal() {
    // 로딩 상태 표시 (옵션)
    document.getElementById('modalCategory').innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> 제미나이 요약';
    document.getElementById('modalTitle').textContent = '주간 주요 뉴스 브리핑 (로딩 중...)';
    document.getElementById('modalSource').innerHTML = `<i class="fa-solid fa-robot"></i> AI 요약 팀`;

    // 날짜는 오늘 날짜로 표시 (또는 파일에서 추출할 수도 있습니다)
    const today = new Date();
    document.getElementById('modalDate').innerHTML = `<i class="fa-regular fa-clock"></i> ${formatDate(today)}`;
    document.getElementById('modalBody').innerHTML = '<div class="spinner" style="margin: 2rem auto;"></div><p style="text-align:center;">브리핑을 불러오는 중입니다...</p>';

    // 모달 띄우기
    modalOverlay.classList.add('active');
    document.body.style.overflow = 'hidden';

    try {
        // 캐시 방지를 위한 타임스탬프
        const timestamp = new Date().getTime();
        const response = await fetch(`data/weekly_briefing.txt?t=${timestamp}`);

        if (!response.ok) {
            throw new Error('브리핑 파일을 찾을 수 없습니다.');
        }

        const textData = await response.text();

        document.getElementById('modalTitle').textContent = '주간 주요 뉴스 브리핑 살펴보기';

        // 간단한 마크다운 파싱 (줄바꿈 및 볼드, 리스트 처리)
        // 1. 줄바꿈 보존을 위해 <br> 로 치환 또는 p 태그로 감싸기
        let formattedHtml = textData
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // **굵게** 처리
            .replace(/\n\n/g, '</p><p>') // 빈 줄은 새 문단으로
            .replace(/\n/g, '<br>'); // 단순 줄바꿈은 <br>로

        // 전체를 p 태그로 감싸기
        if (!formattedHtml.startsWith('<p>')) {
            formattedHtml = '<p>' + formattedHtml + '</p>';
        }

        document.getElementById('modalBody').innerHTML = `<div style="line-height: 1.8; font-size: 1.05rem; color: #e2e8f0; background: rgba(59, 130, 246, 0.05); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(59, 130, 246, 0.2);">${formattedHtml}</div>`;

    } catch (error) {
        document.getElementById('modalTitle').textContent = '브리핑 불러오기 실패';
        document.getElementById('modalBody').innerHTML = `
            <div style="text-align:center; padding: 2rem 0;">
                <i class="fa-solid fa-triangle-exclamation" style="font-size: 3rem; color: #f59e0b; margin-bottom: 1rem;"></i>
                <p>이번 주 브리핑 요약 파일이 아직 준비되지 않았습니다.</p>
                <p style="font-size:0.9rem; color:var(--text-secondary); margin-top:0.5rem;">('data/weekly_briefing.txt' 파일을 확인해주세요)</p>
            </div>
        `;
        console.error(error);
    }
}

// --- 초기화 시점 데이터 패치 로직 ---
async function fetchNewsData(isRefresh = false) {
    try {
        // 캐시 방지를 위해 현재 시간 타임스탬프를 쿼리 파라미터로 추가
        const timestamp = new Date().getTime();
        const url = `data/newsData.json?t=${timestamp}`;

        const response = await fetch(url, {
            cache: 'no-store' // 추가적인 캐시 방지 옵션
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        newsData = await response.json();
    } catch (error) {
        console.error('Failed to load news data, falling back to empty state or dummy.', error);
        // 에러 시 렌더링 할 것이 없으나, 안전을 위해 캐치
    } finally {
        if (!isRefresh) {
            displayDate();
        }
        renderNews(currentCategory);
    }
}

// --- 기사 렌더링 시점 이후 초기화 로직 ---

// 법령 검색 처리 함수
function processLawSearch(query) {
    if (!query || query.trim() === '') return;

    // 국가법령정보센터의 본문 검색 직접 연결 URL
    // lsSc.do와 lsSchType=1(본문검색) 파라미터를 사용하여 통합검색 결과 페이지를 새 창으로 직접 띄웁니다.
    const lawSearchUrl = `https://www.law.go.kr/LSW/lsSc.do?menuId=1&lsSchType=1&query=`;

    // 새 창으로 검색 결과 열기
    window.open(lawSearchUrl + encodeURIComponent(query.trim()), '_blank');
}

// 검색폼 제출 핸들러
function searchLaw(event) {
    event.preventDefault();
    const input = document.getElementById('lawSearchInput');
    processLawSearch(input.value);
}

// 빠른 검색(태그버튼) 핸들러
function quickSearch(keyword) {
    const input = document.getElementById('lawSearchInput');
    input.value = keyword;
    processLawSearch(keyword);
}

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    fetchNewsData();
    initTabs();

    // AI 주간 뉴스 브리핑 배너 클릭 이벤트
    const aiBanner = document.getElementById('aiBriefingBanner');
    if (aiBanner) {
        aiBanner.addEventListener('click', openAIBriefingModal);

        // 접근성을 위한 키보드 이벤트
        aiBanner.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                openAIBriefingModal();
            }
        });
    }

    // 모달 닫기 이벤트 리스너
    closeModalBtn.addEventListener('click', closeNewsModal);

    // 모달 클릭 외부 영역 및 ESC 이벤트
    modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) {
            closeNewsModal();
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modalOverlay.classList.contains('active')) {
            closeNewsModal();
        }
    });

    // 새로고침 버튼 이벤트 연동
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            // 새로고침 중복 클릭 방지 및 시각적 애니메이션 피드백
            if (refreshBtn.classList.contains('is-refreshing')) return;

            refreshBtn.classList.add('is-refreshing');

            // 데이터 재요청 (true 파라미터로 새로고침 모드 전달)
            await fetchNewsData(true);

            // 시각적 피드백을 위해 최소 800ms 애니메이션 유지 후 제거
            setTimeout(() => {
                refreshBtn.classList.remove('is-refreshing');
            }, 800);
        });
    }
});
