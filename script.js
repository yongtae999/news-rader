// 전역 뉴스 데이터 변수
let newsData = { hunting: [], asf: [], ecosystem: [] };

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
        case 'hunting': categoryName = "수렵"; break;
        case 'asf': categoryName = "ASF 동향"; break;
        case 'ecosystem': categoryName = "교란생물"; break;
    }

    // 오늘 업데이트 된 기사면 'N시간 전' 또는 '오늘' 표시 로직 추가 가능하지만 현재는 날짜로 통일
    const publishedDate = calculatePublishedDate(newsItem.daysAgo);
    let isNew = newsItem.daysAgo === 0 ? '<span style="color:var(--accent-color); font-weight:bold; margin-right: 5px;">[새소식]</span>' : '';

    return `
        <a href="#" class="news-card" aria-label="${newsItem.title} 기사 읽기" onclick="openNewsModal(${newsItem.id}); return false;">
            <div class="card-image">
                <span class="card-category-badge">${categoryName}</span>
                <img src="${imageUrl}" alt="기사 섬네일 이미지" loading="lazy">
            </div>
            <div class="card-content">
                <div class="card-meta">
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
                <div class="empty-state">
                    <i class="fa-regular fa-folder-open" style="font-size: 3rem; margin-bottom: 1rem; color: var(--text-secondary);"></i>
                    <p>현재 등록된 뉴스가 없습니다.</p>
                </div>
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

            // 데스크탑 인디케이터 슬라이딩 애니메이션 계산 (탭 3개 기준)
            if (window.innerWidth > 768) {
                indicator.style.transform = `translateX(${index * 100}%)`;
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
                indicator.style.transform = `translateX(${activeIndex * 100}%)`;
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
            if (key === 'hunting') targetCategoryName = '수렵';
            if (key === 'asf') targetCategoryName = 'ASF 동향';
            if (key === 'ecosystem') targetCategoryName = '교란생물';
            break;
        }
    }

    if (!targetNews) return;

    // 2. 모달 내 DOM 엘리먼트에 데이터 주입
    document.getElementById('modalCategory').textContent = targetCategoryName;
    document.getElementById('modalTitle').textContent = targetNews.title;
    document.getElementById('modalSource').innerHTML = `<i class="fa-regular fa-building"></i> ${targetNews.source}`;

    const publishedDate = calculatePublishedDate(targetNews.daysAgo);
    document.getElementById('modalDate').innerHTML = `<i class="fa-regular fa-clock"></i> ${publishedDate}`;

    document.getElementById('modalImage').src = targetNews.image;

    // 본문 내용 생성 (항목별 실제 저장된 상세 body 텍스트 활용)
    const articleBodyHTML = `
        <p><strong>${targetNews.excerpt}</strong></p>
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

// --- 초기화 시점 데이터 패치 로직 ---
async function fetchNewsData() {
    try {
        const response = await fetch('data/newsData.json');
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        newsData = await response.json();
    } catch (error) {
        console.error('Failed to load news data, falling back to empty state or dummy.', error);
        // 에러 시 렌더링 할 것이 없으나, 안전을 위해 캐치
    } finally {
        displayDate();
        renderNews('hunting');
    }
}

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    fetchNewsData();
    initTabs();

    // 모달 닫기 이벤트 리스너
    closeModalBtn.addEventListener('click', closeNewsModal);

    // 모달 외부(딤 처리된 배경) 클릭 시 닫기
    modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) {
            closeNewsModal();
        }
    });

    // ESC 키 입력 시 닫기
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modalOverlay.classList.contains('active')) {
            closeNewsModal();
        }
    });
});
