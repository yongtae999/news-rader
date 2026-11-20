// 전역 뉴스 데이터 및 상태 변수
let newsData = { hunting: [], asf: [], ai: [], ecosystem: [], association: [], editorial: [] };
let currentCategory = 'hunting';
let isScrapMode = false;
let currentSearchQuery = '';
let activeModalNews = null;

// 로컬스토리지 스크랩 키
const SCRAP_STORAGE_KEY = 'kowaps_news_scraps_v1';

// --- 스크랩(북마크) 관리 로직 ---
function getScraps() {
    try {
        const saved = localStorage.getItem(SCRAP_STORAGE_KEY);
        return saved ? JSON.parse(saved) : [];
    } catch (e) {
        console.error('Failed to load scraps:', e);
        return [];
    }
}

function saveScraps(scraps) {
    try {
        localStorage.setItem(SCRAP_STORAGE_KEY, JSON.stringify(scraps));
        updateScrapCountBadge();
    } catch (e) {
        console.error('Failed to save scraps:', e);
    }
}

function isScrapped(newsId) {
    const scraps = getScraps();
    return scraps.some(item => item.id === newsId);
}

function toggleScrap(newsId, event) {
    if (event) {
        event.stopPropagation();
        event.preventDefault();
    }

    const scraps = getScraps();
    const existingIndex = scraps.findIndex(item => item.id === newsId);

    if (existingIndex > -1) {
        // 제거
        scraps.splice(existingIndex, 1);
        saveScraps(scraps);
        showToast('관심 기사 스크랩이 해제되었습니다.');
    } else {
        // 추가 - 전체 뉴스에서 해당 기사 탐색
        let targetItem = null;
        let targetCat = '';
        for (const [cat, items] of Object.entries(newsData)) {
            const found = items.find(it => it.id === newsId);
            if (found) {
                targetItem = { ...found, categoryKey: cat };
                targetCat = cat;
                break;
            }
        }

        if (targetItem) {
            scraps.unshift(targetItem);
            saveScraps(scraps);
            showToast('⭐ 관심 기사로 스크랩되었습니다.');
        }
    }

    // UI 동기화
    updateScrapCountBadge();
    updateCardBookmarkUI(newsId);

    // 모달이 열려있다면 모달 북마크 버튼도 갱신
    if (activeModalNews && activeModalNews.id === newsId) {
        updateModalBookmarkUI(newsId);
    }

    // 스크랩 모드인 경우 목록 재렌더링
    if (isScrapMode) {
        renderNews();
    }
}

function updateScrapCountBadge() {
    const badge = document.getElementById('scrapCountBadge');
    if (badge) {
        const scraps = getScraps();
        badge.textContent = scraps.length;
    }
}

function updateCardBookmarkUI(newsId) {
    const btns = document.querySelectorAll(`.card-bookmark-btn[data-id="${newsId}"]`);
    const isSaved = isScrapped(newsId);
    btns.forEach(btn => {
        btn.classList.toggle('active', isSaved);
        btn.innerHTML = isSaved ? '<i class="fa-solid fa-bookmark"></i>' : '<i class="fa-regular fa-bookmark"></i>';
        btn.setAttribute('aria-label', isSaved ? '스크랩 해제' : '스크랩 저장');
    });
}

function updateModalBookmarkUI(newsId) {
    const btn = document.getElementById('modalBookmarkBtn');
    if (btn) {
        const isSaved = isScrapped(newsId);
        btn.classList.toggle('active', isSaved);
        btn.innerHTML = isSaved ? '<i class="fa-solid fa-bookmark"></i>' : '<i class="fa-regular fa-bookmark"></i>';
    }
}

// --- 토스트 알림 메시지 ---
let toastTimer = null;
function showToast(message) {
    const toast = document.getElementById('toastMessage');
    if (!toast) return;

    toast.textContent = message;
    toast.classList.add('show');

    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
        toast.classList.remove('show');
    }, 2400);
}

// --- 날짜 표시 영역 ---
function formatDate(date) {
    const year = date.getFullYear().toString().slice(2);
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}.${month}.${day}`;
}

function displayDate() {
    const today = new Date();
    const dateElement = document.getElementById('currentDate');
    if (!dateElement) return;
    const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'short' };
    const dateString = today.toLocaleDateString('ko-KR', options);

    dateElement.innerHTML = `<i class="fa-regular fa-calendar-check"></i> ${dateString}`;
}

function handleGoBack() {
    if (window.history.length > 1 && document.referrer) {
        window.history.back();
    } else {
        window.location.href = '../task-assistant/index.html';
    }
}

function calculatePublishedDate(daysAgo) {
    const today = new Date();
    today.setDate(today.getDate() - (daysAgo || 0));
    return formatDate(today);
}

// 카테고리 한글명 반환
function getCategoryLabel(catKey) {
    const map = {
        'hunting': '수렵관련',
        'asf': 'ASF관련',
        'ai': '조류인플루엔자(AI)',
        'ecosystem': '교란생물 관련',
        'association': '협회 관련',
        'editorial': '사설/기획'
    };
    return map[catKey] || '일반뉴스';
}

function stripHtmlTags(html) {
    return (html || '').replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
}

function escapeHtml(str) {
    return (str || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function cleanArticleBody(rawBody) {
    if (!rawBody) return '상세 본문 내용이 없습니다.';
    let cleaned = String(rawBody)
        .replace(/네이버\s*뉴스\s*검색\s*결과입니다\.?\s*(?:<br\s*\/?>\s*)*/gi, '')
        .replace(/(?:<br\s*\/?>\s*)*<a\b[^>]*>\s*원문\s*기사\s*보러가기[^<]*<\/a>\s*/gi, '')
        .replace(/^(?:\s*<br\s*\/?>\s*)+|(?:\s*<br\s*\/?>\s*)+$/gi, '')
        .trim();

    // 남아있는 외부 링크가 있다면 새 탭 열기 및 보안 속성 보강
    cleaned = cleaned.replace(/<a\b([^>]*)>/gi, (match, attrs) => {
        let updated = attrs;
        if (!/target\s*=/i.test(updated)) {
            updated += ' target="_blank"';
        }
        if (!/rel\s*=/i.test(updated)) {
            updated += ' rel="noopener noreferrer"';
        }
        return `<a${updated}>`;
    });

    return cleaned || '상세 본문 내용이 없습니다.';
}

function resetNewsSearch() {
    const searchInput = document.getElementById('newsSearchInput');
    const clearBtn = document.getElementById('clearSearchBtn');
    if (searchInput) {
        searchInput.value = '';
        searchInput.focus();
    }
    currentSearchQuery = '';
    if (clearBtn) clearBtn.style.display = 'none';
    renderNews();
}

// 뉴스 카드 생성 함수
function createNewsCard(newsItem, index) {
    const categoryName = getCategoryLabel(newsItem.categoryKey || currentCategory);
    const publishedDate = newsItem.date || calculatePublishedDate(newsItem.daysAgo);
    const isNew = newsItem.daysAgo === 0 ? '<span class="badge-new">[새소식]</span> ' : '';
    const isSaved = isScrapped(newsItem.id);

    return `
        <div class="news-card" onclick="openNewsModal(${newsItem.id})">
            <button class="card-bookmark-btn ${isSaved ? 'active' : ''}" data-id="${newsItem.id}" onclick="toggleScrap(${newsItem.id}, event)" aria-label="${isSaved ? '스크랩 해제' : '스크랩 저장'}" title="${isSaved ? '스크랩 해제' : '스크랩 저장'}">
                <i class="fa-${isSaved ? 'solid' : 'regular'} fa-bookmark"></i>
            </button>
            <div class="card-content">
                <div class="card-meta">
                    <span class="card-category-badge">${categoryName}</span>
                    <span class="card-source"><i class="fa-regular fa-building"></i> ${newsItem.source || '네이버 뉴스'}</span>
                    <span class="card-date"><i class="fa-regular fa-clock"></i> ${publishedDate}</span>
                </div>
                <h2 class="card-title">${isNew}${newsItem.title}</h2>
                <p class="card-excerpt">${newsItem.excerpt}</p>
                <div class="card-footer">
                    <span>자세히 보기</span>
                    <i class="fa-solid fa-arrow-right"></i>
                </div>
            </div>
        </div>
    `;
}

// 스켈레톤 로딩 HTML 생성
function renderSkeletonLoading() {
    const newsListContainer = document.getElementById('newsList');
    if (!newsListContainer) return;

    let skeletonHTML = '';
    for (let i = 0; i < 6; i++) {
        skeletonHTML += `
            <div class="skeleton-card">
                <div class="skeleton-line sm" style="width: 30%;"></div>
                <div class="skeleton-line lg" style="width: 85%;"></div>
                <div class="skeleton-line md" style="width: 95%;"></div>
                <div class="skeleton-line md" style="width: 60%;"></div>
                <div class="skeleton-footer"></div>
            </div>
        `;
    }
    newsListContainer.innerHTML = skeletonHTML;
}

// 뉴스 렌더링 로직
function renderNews() {
    const newsListContainer = document.getElementById('newsList');
    if (!newsListContainer) return;

    let sourceItems = [];

    if (isScrapMode) {
        sourceItems = getScraps();
    } else {
        sourceItems = newsData[currentCategory] || [];
    }

    // 검색어 필터링 적용
    if (currentSearchQuery.trim() !== '') {
        const query = currentSearchQuery.trim().toLowerCase();

        sourceItems = sourceItems.filter(item => {
            const titleMatch = (item.title || '').toLowerCase().includes(query);
            const excerptMatch = (item.excerpt || '').toLowerCase().includes(query);
            const bodyMatch = stripHtmlTags(item.body).toLowerCase().includes(query);
            const sourceMatch = (item.source || '').toLowerCase().includes(query);
            return titleMatch || excerptMatch || bodyMatch || sourceMatch;
        });
    }

    // 날짜 최신순 정렬
    const sortedItems = [...sourceItems].sort((a, b) => (a.daysAgo || 0) - (b.daysAgo || 0));

    if (sortedItems.length > 0) {
        newsListContainer.innerHTML = sortedItems.map((item, index) => createNewsCard(item, index)).join('');
    } else {
        if (isScrapMode) {
            newsListContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fa-regular fa-bookmark empty-icon"></i>
                    <h3>스크랩된 기사가 없습니다.</h3>
                    <p>기사 카드의 북마크 아이콘을 터치하여 관심 기사를 저장해 보세요.</p>
                </div>
            `;
        } else if (currentSearchQuery.trim() !== '') {
            newsListContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-magnifying-glass empty-icon"></i>
                    <h3>'${escapeHtml(currentSearchQuery)}' 검색 결과가 없습니다.</h3>
                    <p>다른 검색어를 입력하시거나 검색어를 초기화해 보세요.</p>
                    <button type="button" class="empty-reset-btn" onclick="resetNewsSearch()">
                        <i class="fa-solid fa-rotate-left"></i> 검색 초기화
                    </button>
                </div>
            `;
        } else {
            newsListContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fa-regular fa-folder-open empty-icon"></i>
                    <h3>현재 등록된 뉴스가 없습니다.</h3>
                    <p>잠시 후 새로고침 버튼을 눌러 최신 뉴스를 확인해 주세요.</p>
                </div>
            `;
        }
    }
}

// 탭 전환 핸들러
function initTabs() {
    const tabs = document.querySelectorAll('.tab-button');
    const indicator = document.querySelector('.tab-indicator');
    const scrapFilterBtn = document.getElementById('scrapFilterBtn');

    tabs.forEach((tab, index) => {
        tab.addEventListener('click', () => {
            // 스크랩 모드 해제
            if (isScrapMode) {
                isScrapMode = false;
                if (scrapFilterBtn) scrapFilterBtn.classList.remove('active');
            }

            if (tab.classList.contains('active') && !isScrapMode) return;

            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            updateIndicatorPosition();

            currentCategory = tab.getAttribute('data-category');
            
            // 서브탭 및 맵 컨테이너 처리
            handleSubTabVisibility();

            // 스켈레톤 로딩 후 렌더링
            renderSkeletonLoading();
            setTimeout(renderNews, 200);
        });
    });

    // 스크랩 필터 버튼 클릭
    if (scrapFilterBtn) {
        scrapFilterBtn.addEventListener('click', () => {
            isScrapMode = !isScrapMode;
            scrapFilterBtn.classList.toggle('active', isScrapMode);

            if (isScrapMode) {
                tabs.forEach(t => t.classList.remove('active'));
                if (indicator) indicator.style.transform = 'scale(0)';
            } else {
                const activeTab = document.querySelector(`.tab-button[data-category="${currentCategory}"]`);
                if (activeTab) activeTab.classList.add('active');
                updateIndicatorPosition();
            }

            handleSubTabVisibility();
            renderSkeletonLoading();
            setTimeout(renderNews, 150);
        });
    }

    window.addEventListener('resize', updateIndicatorPosition);
    requestAnimationFrame(updateIndicatorPosition);
}

function updateIndicatorPosition() {
    const indicator = document.querySelector('.tab-indicator');
    const activeTab = document.querySelector('.tab-button.active');
    if (!indicator) return;

    if (window.innerWidth <= 768 || isScrapMode || !activeTab) {
        indicator.style.opacity = '0';
        indicator.style.width = '0px';
    } else {
        indicator.style.opacity = '1';
        indicator.style.width = `${activeTab.offsetWidth}px`;
        indicator.style.transform = `translateX(${activeTab.offsetLeft}px)`;
    }
}

function handleSubTabVisibility() {
    const asfSubTabs = document.getElementById('asfSubTabs');
    const asfStatusMap = document.getElementById('asfStatusMap');
    const aiSubTabs = document.getElementById('aiSubTabs');
    const aiStatusMap = document.getElementById('aiStatusMap');
    const newsListDisplay = document.getElementById('newsList');

    if (asfSubTabs) asfSubTabs.style.display = 'none';
    if (asfStatusMap) asfStatusMap.style.display = 'none';
    if (aiSubTabs) aiSubTabs.style.display = 'none';
    if (aiStatusMap) aiStatusMap.style.display = 'none';
    if (newsListDisplay) newsListDisplay.style.display = 'grid';

    if (isScrapMode) return;

    if (currentCategory === 'asf') {
        if (asfSubTabs) {
            asfSubTabs.style.display = 'flex';
            resetSubTabs('asfSubTabs');
        }
    } else if (currentCategory === 'ai') {
        if (aiSubTabs) {
            aiSubTabs.style.display = 'flex';
            resetSubTabs('aiSubTabs');
        }
    }
}

function resetSubTabs(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const btns = container.querySelectorAll('.sub-tab-btn');
    btns.forEach((btn, idx) => {
        btn.classList.toggle('active', idx === 0);
    });
}

// 서브 탭 동작 핸들러
function initSubTabs() {
    const subTabs = document.querySelectorAll('.sub-tab-btn');

    subTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            if (tab.classList.contains('active')) return;

            const parentContainer = tab.parentElement;
            parentContainer.querySelectorAll('.sub-tab-btn').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const target = tab.getAttribute('data-target');
            const category = parentContainer.id === 'asfSubTabs' ? 'asf' : 'ai';
            const mapContainer = category === 'asf' ? document.getElementById('asfStatusMap') : document.getElementById('aiStatusMap');
            const newsListDisplay = document.getElementById('newsList');

            if (target === 'news') {
                if (mapContainer) mapContainer.style.display = 'none';
                if (newsListDisplay) newsListDisplay.style.display = 'grid';
                renderNews();
            } else if (target === 'map') {
                if (newsListDisplay) newsListDisplay.style.display = 'none';
                if (mapContainer) mapContainer.style.display = 'block';
            }
        });
    });
}

// 검색 기능 핸들러
function initSearch() {
    const searchInput = document.getElementById('newsSearchInput');
    const clearBtn = document.getElementById('clearSearchBtn');

    if (!searchInput) return;

    searchInput.addEventListener('input', (e) => {
        currentSearchQuery = e.target.value;
        if (clearBtn) {
            clearBtn.style.display = currentSearchQuery.length > 0 ? 'block' : 'none';
        }
        renderNews();
    });

    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            searchInput.value = '';
            currentSearchQuery = '';
            clearBtn.style.display = 'none';
            searchInput.focus();
            renderNews();
        });
    }
}

// 모달 동작 스크립트
const modalOverlay = document.getElementById('newsModal');
const closeModalBtn = document.getElementById('closeModal');

function openNewsModal(newsId) {
    let targetNews = null;
    let targetCategoryName = '';

    // 1. 전체 뉴스 데이터 및 스크랩 데이터에서 탐색
    for (const [key, items] of Object.entries(newsData)) {
        const found = items.find(item => item.id === newsId);
        if (found) {
            targetNews = found;
            targetCategoryName = getCategoryLabel(key);
            break;
        }
    }

    if (!targetNews) {
        const scraps = getScraps();
        const foundInScrap = scraps.find(item => item.id === newsId);
        if (foundInScrap) {
            targetNews = foundInScrap;
            targetCategoryName = getCategoryLabel(foundInScrap.categoryKey || 'hunting');
        }
    }

    if (!targetNews) return;
    activeModalNews = targetNews;

    // 2. DOM에 데이터 주입
    document.getElementById('modalCategory').textContent = targetCategoryName;
    document.getElementById('modalTitle').textContent = targetNews.title;
    document.getElementById('modalSource').innerHTML = `<i class="fa-regular fa-building"></i> ${targetNews.source || '네이버 뉴스'}`;

    const publishedDate = targetNews.date || calculatePublishedDate(targetNews.daysAgo);
    document.getElementById('modalDate').innerHTML = `<i class="fa-regular fa-clock"></i> ${publishedDate}`;

    // 본문 내용 렌더링 (잔여 안내 문구 및 중복 링크 정리)
    const cleanedBody = cleanArticleBody(targetNews.body);
    const articleBodyHTML = `
        <div class="modal-body-excerpt">
            <p>${targetNews.excerpt || ''}</p>
        </div>
        <div class="modal-body-content">
            <p>${cleanedBody}</p>
        </div>
    `;
    document.getElementById('modalBody').innerHTML = articleBodyHTML;

    // 원문 링크 및 북마크 버튼 설정
    const originalLinkBtn = document.getElementById('modalOriginalLink');
    if (originalLinkBtn) {
        if (targetNews.link) {
            originalLinkBtn.href = targetNews.link;
            originalLinkBtn.setAttribute('target', '_blank');
            originalLinkBtn.setAttribute('rel', 'noopener noreferrer');
            originalLinkBtn.style.display = 'inline-flex';
        } else {
            originalLinkBtn.style.display = 'none';
        }
    }

    const bookmarkBtn = document.getElementById('modalBookmarkBtn');
    if (bookmarkBtn) {
        bookmarkBtn.style.display = 'flex';
        bookmarkBtn.onclick = () => toggleScrap(targetNews.id);
        updateModalBookmarkUI(targetNews.id);
    }

    // 모달 액션 영역 노출
    const modalFooter = document.getElementById('modalFooter');
    if (modalFooter) modalFooter.style.display = 'flex';

    // 3. 모달 활성화 및 배경 고정
    const overlay = document.getElementById('newsModal');
    if (overlay) {
        overlay.classList.add('active');
        overlay.setAttribute('aria-hidden', 'false');
    }
    document.body.style.overflow = 'hidden';
}

function openOfficialImageModal(imgSrc, titleText) {
    document.getElementById('modalCategory').innerHTML = '<i class="fa-solid fa-map-location-dot"></i> ASF 공식 자료';
    document.getElementById('modalTitle').textContent = titleText;
    document.getElementById('modalSource').innerHTML = '<i class="fa-regular fa-building"></i> 국립야생동물질병관리원 WADIS';
    document.getElementById('modalDate').innerHTML = '<i class="fa-regular fa-clock"></i> 26.11.20 기준';
    document.getElementById('modalBody').innerHTML = `
        <div style="text-align:center;">
            <img src="${escapeHtml(imgSrc)}" alt="${escapeHtml(titleText)}" style="width:100%; height:auto; border-radius:10px; border:1px solid rgba(255,255,255,0.12); display:block; margin:0 auto;">
        </div>
    `;

    const bookmarkBtn = document.getElementById('modalBookmarkBtn');
    if (bookmarkBtn) bookmarkBtn.style.display = 'none';

    const copyBtn = document.getElementById('modalCopyLinkBtn');
    if (copyBtn) copyBtn.style.display = 'none';

    const originalLinkBtn = document.getElementById('modalOriginalLink');
    if (originalLinkBtn) {
        originalLinkBtn.href = imgSrc;
        originalLinkBtn.setAttribute('target', '_blank');
        originalLinkBtn.setAttribute('rel', 'noopener noreferrer');
        originalLinkBtn.innerHTML = '<i class="fa-solid fa-arrow-up-right-from-square"></i> 새 탭에서 원본 크게 보기';
        originalLinkBtn.style.display = 'inline-flex';
    }

    const modalFooter = document.getElementById('modalFooter');
    if (modalFooter) modalFooter.style.display = 'flex';

    const overlay = document.getElementById('newsModal');
    if (overlay) {
        overlay.classList.add('active');
        overlay.setAttribute('aria-hidden', 'false');
    }
    document.body.style.overflow = 'hidden';
}

function closeNewsModal() {
    const overlay = document.getElementById('newsModal');
    if (!overlay) return;
    overlay.classList.remove('active');
    overlay.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    activeModalNews = null;

    // 이미지 모달 열람 후 뉴스 모달 버튼 상태 원복
    const copyBtn = document.getElementById('modalCopyLinkBtn');
    if (copyBtn) copyBtn.style.display = 'flex';
    const originalLinkBtn = document.getElementById('modalOriginalLink');
    if (originalLinkBtn) {
        originalLinkBtn.innerHTML = '<i class="fa-solid fa-arrow-up-right-from-square"></i> 원문 기사 보러가기';
    }
}

function copyCurrentNewsLink() {
    if (!activeModalNews || !activeModalNews.link) {
        showToast('복사할 링크가 없습니다.');
        return;
    }

    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(activeModalNews.link).then(() => {
            showToast('📋 기사 원문 링크가 클립보드에 복사되었습니다.');
        }).catch(() => {
            showToast('링크 복사에 실패했습니다.');
        });
    } else {
        // Fallback
        const textarea = document.createElement('textarea');
        textarea.value = activeModalNews.link;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showToast('📋 기사 원문 링크가 복사되었습니다.');
    }
}

// 주간 AI 브리핑 모달 열기 함수
async function openAIBriefingModal() {
    document.getElementById('modalCategory').innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Gemini AI 요약';
    document.getElementById('modalTitle').textContent = '주간 주요 야생생물 종합 동향 브리핑';
    document.getElementById('modalSource').innerHTML = `<i class="fa-solid fa-robot"></i> AI 분석관`;

    const today = new Date();
    document.getElementById('modalDate').innerHTML = `<i class="fa-regular fa-clock"></i> ${formatDate(today)}`;
    document.getElementById('modalBody').innerHTML = `
        <div class="briefing-loading-spinner">
            <div class="spinner"></div>
            <p>Gemini AI 주간 브리핑을 불러오는 중입니다...</p>
        </div>
    `;

    // 모달 푸터 숨김(AI 브리핑에서는 일반 기사 원문 링크 불필요)
    const modalFooter = document.getElementById('modalFooter');
    if (modalFooter) modalFooter.style.display = 'none';

    const modalBookmarkBtn = document.getElementById('modalBookmarkBtn');
    if (modalBookmarkBtn) modalBookmarkBtn.style.display = 'none';

    const overlay = document.getElementById('newsModal');
    if (overlay) {
        overlay.classList.add('active');
        overlay.setAttribute('aria-hidden', 'false');
    }
    document.body.style.overflow = 'hidden';

    try {
        const timestamp = new Date().getTime();
        const response = await fetch(`data/weekly_briefing.txt?t=${timestamp}`);

        if (!response.ok) {
            throw new Error('브리핑 파일을 찾을 수 없습니다.');
        }

        const textData = await response.text();

        // 텍스트 마크다운 파싱 및 카드형 스타일링
        let formattedHtml = textData
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n\n/g, '</div><div class="briefing-card-section">')
            .replace(/\n/g, '<br>');

        formattedHtml = `<div class="briefing-container"><div class="briefing-card-section">${formattedHtml}</div></div>`;

        document.getElementById('modalBody').innerHTML = formattedHtml;

    } catch (error) {
        document.getElementById('modalTitle').textContent = '브리핑 불러오기';
        document.getElementById('modalBody').innerHTML = `
            <div class="briefing-empty-state">
                <i class="fa-solid fa-triangle-exclamation"></i>
                <p>이번 주 AI 뉴스 브리핑 파일이 아직 준비되지 않았습니다.</p>
                <span>매주 목요일 최신 브리핑이 자동 갱신됩니다.</span>
            </div>
        `;
        console.error(error);
    }
}

// --- 데이터 패치 로직 ---
async function fetchNewsData(isRefresh = false) {
    if (!isRefresh) {
        renderSkeletonLoading();
    }

    try {
        const timestamp = new Date().getTime();
        const url = `data/newsData.json?t=${timestamp}`;

        const response = await fetch(url, { cache: 'no-store' });
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        newsData = await response.json();
    } catch (error) {
        console.warn('News data fetch fallback:', error);
    } finally {
        if (!isRefresh) {
            displayDate();
            updateScrapCountBadge();
        }
        renderNews();
    }
}

// 법령 검색 처리
function processLawSearch(query) {
    if (!query || query.trim() === '') return;
    const lawSearchUrl = `https://www.law.go.kr/LSW/lsSc.do?menuId=1&lsSchType=1&query=`;
    window.open(lawSearchUrl + encodeURIComponent(query.trim()), '_blank', 'noopener,noreferrer');
}

function searchLaw(event) {
    event.preventDefault();
    const input = document.getElementById('lawSearchInput');
    if (input) processLawSearch(input.value);
}

function quickSearch(keyword) {
    const input = document.getElementById('lawSearchInput');
    if (input) input.value = keyword;
    processLawSearch(keyword);
}

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    fetchNewsData();
    initTabs();
    initSubTabs();
    initSearch();

    // AI 주간 브리핑 배너 이벤트
    const aiBanner = document.getElementById('aiBriefingBanner');
    if (aiBanner) {
        aiBanner.addEventListener('click', openAIBriefingModal);
        aiBanner.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                openAIBriefingModal();
            }
        });
    }

    // 모달 닫기 이벤트 리스너 (뉴스 상세 모달 & AI 브리핑 모달 통합)
    const overlay = document.getElementById('newsModal');
    const closeBtn = document.getElementById('closeModal');
    if (closeBtn) {
        closeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            closeNewsModal();
        });
    }

    if (overlay) {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeNewsModal();
        });
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const activeOverlay = document.getElementById('newsModal');
            if (activeOverlay && activeOverlay.classList.contains('active')) {
                closeNewsModal();
            }
        }
    });

    // 발생현황 iframe 자동 높이 조절 및 공식 이미지 모달 연동
    window.addEventListener('message', (event) => {
        if (!event.data) return;

        if (event.data.type === 'statusIframeHeight') {
            const targetId = event.data.source === 'asf' ? 'asfStatusIframe' : event.data.source === 'ai' ? 'aiStatusIframe' : null;
            if (!targetId) return;
            const iframe = document.getElementById(targetId);
            if (iframe && typeof event.data.height === 'number' && event.data.height > 300) {
                iframe.style.height = `${Math.ceil(event.data.height) + 16}px`;
            }
            return;
        }

        if (event.data.type === 'openImageModal' && event.data.src) {
            openOfficialImageModal(event.data.src, event.data.title || '공식 발생현황 지도 원본');
        }
    });

    // 새로고침 버튼 이벤트
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            if (refreshBtn.classList.contains('is-refreshing')) return;

            refreshBtn.classList.add('is-refreshing');
            showToast('🔄 최신 뉴스를 새로고침 중입니다...');

            await fetchNewsData(true);

            setTimeout(() => {
                refreshBtn.classList.remove('is-refreshing');
                showToast('✅ 최신 뉴스 동기화가 완료되었습니다.');
            }, 600);
        });
    }
});
