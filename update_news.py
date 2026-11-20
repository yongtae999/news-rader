import urllib.request
import urllib.parse
import json
import os
from datetime import datetime, timezone, timedelta
import re

# 네이버 API 인증 정보 (GitHub Secrets 또는 환경 변수)
client_id = os.environ.get("NAVER_CLIENT_ID", "")
client_secret = os.environ.get("NAVER_CLIENT_SECRET", "")

# 2026년 기준 실무 키워드 및 카테고리 매핑
categories = {
    # 수렵 탭: 포획, 엽사, 총기안전, 법령 및 지침
    "hunting": [
        "유해조수 포획단", "수렵면허", "총기 안전 수렵", "야생동물 포획", 
        "수렵 관련 법령", "수렵 지침", "야생생물법", "피해방지단", 
        "유해야생동물 기동포획단", "불법엽구", "창애", "올무", 
        "밀렵 단속", "밀거래 단속", "밀렵 특별단속", "수렵장 운영", "야생동물 포획 포상금"
    ],
    # ASF 탭: 멧돼지 및 돼지열병 방역
    "asf": [
        "아프리카돼지열병 멧돼지", "ASF 멧돼지", "야생멧돼지 아프리카돼지열병",
        "멧돼지 폐사체", "ASF 방역울타리", "멧돼지 열화상 드론", "ASF 백신 멧돼지"
    ],
    # AI 탭: 야생조류 AI 및 철새도래지
    "ai": [
        "야생조류 조류인플루엔자", "고병원성 AI 야생조류", "철새 조류인플루엔자",
        "철새도래지 AI", "야생조류 분변 검사 AI", "야생조류 폐사체 AI"
    ],
    # 생태계교란 탭: 뉴트리아, 가시박, 교란어종 및 외래종
    "ecosystem": [
        "생태계교란생물", "교란식물", "교란어종", "교란종", "가시박", 
        "단풍잎돼지풀", "베스", "블루길", "뉴트리아 포획", "황소개구리 퇴치",
        "가시상추", "미국가재", "외래생물 퇴치"
    ],
    # 협회 관련 탭: 지부/지회 활동 및 수렵면허 시험
    "association": [
        "야생생물관리협회", "야생생물 관리협회", "야생생물관리협회 지부", 
        "야생생물관리협회 지회", "야생생물관리협회 밀렵감시단", "밀렵 감시단", 
        "수렵면허시험", "야생생물보호구역"
    ],
    # 사설/기획 탭: 심층 기획 및 전문가 기고
    "editorial": [
        "야생동물 사설", "야생동물 기고", "야생동물 칼럼", "유해조수 기획", 
        "수렵 기획", "생태계 기획", "야생동물 보호 사설"
    ]
}

# 생태계교란생물 탭 노이즈 제외 키워드 (화학·의학·환경호르몬 기사 차단)
ECOSYSTEM_EXCLUDE_KEYWORDS = [
    "내분비계", "교란물질", "환경호르몬", "호르몬",
    "플라스틱", "미세플라스틱", "비스페놀", "프탈레이트", "화장품"
]

# 주요 언론사 도메인 -> 한글 언론사명 폴백 매핑
DOMAIN_SOURCE_MAP = {
    "yna.co.kr": "연합뉴스",
    "newsis.com": "뉴시스",
    "news1.kr": "뉴스1",
    "chosun.com": "조선일보",
    "joongang.co.kr": "중앙일보",
    "donga.com": "동아일보",
    "hani.co.kr": "한겨레",
    "khan.co.kr": "경향신문",
    "hankookilbo.com": "한국일보",
    "kmib.co.kr": "국민일보",
    "seoul.co.kr": "서울신문",
    "segye.com": "세계일보",
    "munhwa.com": "문화일보",
    "mk.co.kr": "매일경제",
    "hankyung.com": "한국경제",
    "sedaily.com": "서울경제",
    "fnnews.com": "파이낸셜뉴스",
    "mt.co.kr": "머니투데이",
    "edaily.co.kr": "이데일리",
    "asiae.co.kr": "아시아경제",
    "ajunews.com": "아주경제",
    "kbs.co.kr": "KBS",
    "imbc.com": "MBC",
    "sbs.co.kr": "SBS",
    "ytn.co.kr": "YTN",
    "jtbc.co.kr": "JTBC",
    "mbn.co.kr": "MBN",
    "joongboo.com": "중부일보",
    "jbnews.com": "중부매일",
    "kyeongin.com": "경인일보",
    "kyeonggi.com": "경기일보",
    "busan.com": "부산일보",
    "imaeil.com": "매일신문",
    "yeongnam.com": "영남일보",
    "kwnews.co.kr": "강원일보",
    "kado.net": "강원도민일보",
    "daejonilbo.com": "대전일보",
    "cctoday.co.kr": "충청투데이",
    "ccdailynews.com": "충청일보",
    "ccdn.co.kr": "충청매일",
    "namdonews.com": "남도일보",
    "kjdaily.com": "광주매일신문",
    "jjan.kr": "전북일보",
    "knnews.co.kr": "경남신문",
    "idomin.com": "경남도민일보",
    "gndomin.com": "경남도민신문",
    "newsgn.com": "뉴스경남",
    "iusm.co.kr": "울산매일",
    "jejunews.com": "제주일보",
    "aflnews.co.kr": "농수축산신문",
    "agrinet.co.kr": "한국농어민신문",
    "nongmin.com": "농민신문",
    "pigpeople.net": "돼지와사람",
    "dailyvet.co.kr": "데일리벳",
    "gukjenews.com": "국제뉴스",
    "newscj.com": "천지일보",
    "dkilbo.com": "대경일보",
    "ggilbo.com": "금강일보",
}

# 뉴스 이미지 매핑
image_mapping = {
    "hunting": ["images/env_gov.png", "images/hunter.png", "images/police.png"],
    "asf": ["images/boar.png", "images/env_gov.png", "images/hunter.png"],
    "ai": ["images/bird_flu.png", "images/env_gov.png"],
    "ecosystem": ["images/env_gov.png", "images/nutria.png", "images/bullfrog.png", "images/hunter.png"],
    "association": ["images/env_gov.png"],
    "editorial": ["images/env_gov.png"]
}

def clean_html(raw_html):
    """HTML 태그 제거 및 특수문자 변환"""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    cleantext = cleantext.replace('&quot;', '"').replace('&apos;', "'").replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    return cleantext.strip()

def get_best_image(category, title, description):
    """기사 제목과 내용을 분석하여 가장 적합한 이미지를 반환합니다."""
    combined_text = title + " " + description
    
    # 1. 특정 키워드에 대한 우선 매칭
    if any(k in combined_text for k in ["경찰", "순찰", "단속", "총기", "불법엽구", "창애", "올무", "밀렵", "법령", "지침", "야생생물법", "포상금"]):
        return "images/police.png"
    if any(k in combined_text for k in ["조류독감", "조류인플루엔자", "철새", "야생조류"]) or "AI" in combined_text.upper():
        return "images/bird_flu.png"
    if any(k in combined_text for k in ["멧돼지", "돼지열병"]) or "ASF" in combined_text.upper():
        return "images/boar.png"
    if any(k in combined_text for k in ["뉴트리아", "괴물쥐"]):
        return "images/nutria.png"
    if any(k in combined_text for k in ["개구리", "거북", "배스", "블루길", "미국가재", "가시박"]):
        return "images/bullfrog.png"
    if any(k in combined_text for k in ["수렵", "엽사", "포획단", "사냥", "포획"]):
        return "images/hunter.png"
    if any(k in combined_text for k in ["환경부", "정부", "지자체", "환경청", "국립생태원"]):
        return "images/env_gov.png"
        
    # 2. 카테고리별 Fallback 이미지
    fallback_map = {
        "hunting": "images/hunter.png",
        "asf": "images/boar.png",
        "ai": "images/bird_flu.png",
        "ecosystem": "images/bullfrog.png",
        "association": "images/env_gov.png",
        "editorial": "images/env_gov.png"
    }
    return fallback_map.get(category, "images/env_gov.png")

def get_bigrams(text):
    """문자열에서 2글자 단위(바이그램) 세트를 추출하여 반환 (유사도 비교용)"""
    text = re.sub(r'[\W_]+', '', text)
    if len(text) < 2:
        return set()
    return set(text[i:i+2] for i in range(len(text)-1))

def clean_source_name(raw_name, original_link=""):
    """언론사명에서 슬로건을 제거하고 깨짐/1글자/특수문자 오류를 도메인 폴백으로 보정합니다."""
    if raw_name:
        cleaned = clean_html(str(raw_name)).strip()
        # 슬로건 구분자(' - ', ' | ', ' :: ', ' : ', ' – ', ' — ') 뒤 텍스트 제거
        cleaned = re.split(r'\s*(?:\s-\s|\s–\s|\s—\s|\s\|\s|\s::\s|\s:\s)\s*', cleaned)[0].strip()
        cleaned = re.sub(r'^[\W_]+|[\W_]+$', '', cleaned).strip()
        # 2글자 이상의 유효한 한글/영문/숫자 포함 여부 검증 (예: 'L', 특수문자 단독 차단)
        valid_chars = re.sub(r'[^가-힣a-zA-Z0-9]', '', cleaned)
        if len(valid_chars) >= 2:
            return cleaned

    # 도메인 기반 매핑 폴백
    if original_link:
        try:
            netloc = urllib.parse.urlparse(original_link).netloc.lower()
            netloc = re.sub(r'^(?:www\.|m\.|news\.)', '', netloc)
            if netloc:
                for dom_key, kor_name in DOMAIN_SOURCE_MAP.items():
                    if netloc == dom_key or netloc.endswith("." + dom_key):
                        return kor_name
                if len(re.sub(r'[^a-zA-Z0-9]', '', netloc)) >= 2:
                    return netloc
        except Exception:
            pass

    return "언론사"

def extract_source_name(link, original_link):
    """주어진 링크(네이버 뉴스 또는 원문)에서 출처(언론사) 이름을 안전하게 추출·정제합니다."""
    # 1. 네이버 뉴스 링크인 경우 HTML에서 추출
    if link.startswith("https://n.news.naver.com"):
        try:
            req = urllib.request.Request(link, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            res = urllib.request.urlopen(req, timeout=2.5)
            html = res.read().decode('utf-8', errors='ignore')
            
            m = re.search(r'twitter:creator"\s+content="([^"]+)"', html, re.I)
            if m:
                return clean_source_name(m.group(1), original_link)
                
            m = re.search(r'property="og:article:author"\s+content="([^"]+)"', html, re.I)
            if m:
                author = m.group(1).split('|')[0].strip()
                if author:
                    return clean_source_name(author, original_link)
        except Exception:
            pass

    # 2. 원문 링크에서 og:site_name 추출 시도 후 정제
    if original_link:
        try:
            req = urllib.request.Request(original_link, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            res = urllib.request.urlopen(req, timeout=2.5)
            html = res.read().decode('utf-8', errors='ignore')
            m = re.search(r'property="og:site_name"\s+content="([^"]+)"', html, re.I)
            if m:
                return clean_source_name(m.group(1), original_link)
        except Exception:
            pass
        return clean_source_name("", original_link)
        
    return "언론사"

def strip_title_prefix(title):
    """제목 앞의 [지역소식], [단신], [포토] 등 말머리 태그를 제거합니다."""
    return re.sub(r'^\s*(?:\[[^\]]{1,16}\]|\([^)]{1,16}\)|【[^】]{1,16}】)\s*', '', title).strip()

def extract_capture_recruit_signature(title, desc):
    """지자체 포획단·피해방지단 모집/운영/교육 보도자료의 중복 판별 시그니처를 추출합니다."""
    text = title + " " + desc
    if not any(k in text for k in ["포획단", "피해방지단"]):
        return None
    if not any(k in text for k in ["모집", "운영", "안전교육", "발대식", "위촉", "선발"]):
        return None
    # 시·군·구 지자체명 추출
    m = re.search(r'([가-힣]{2,4}(?:시|군|구))', title) or re.search(r'([가-힣]{2,4}(?:시|군|구))', desc)
    if not m:
        return None
    region = m.group(1)
    action = next((k for k in ["모집", "안전교육", "운영", "발대식", "위촉", "선발"] if k in text), "")
    return f"{region}:{action}"

def parse_yy_mm_dd(date_str):
    try:
        return datetime.strptime(date_str, "%y.%m.%d").date()
    except Exception:
        return None

def is_duplicate_article(new_title, new_desc, new_date, seen_articles):
    """새 기사가 기존 수집된 기사들과 중복(보도자료 복붙·지역소식/단신·포획단 모집 중복 포함)인지 판별"""
    # [지역소식]·단신 모음 기사는 주제 분산 및 노이즈가 많으므로 제외
    roundup_tags = ["[지역소식]", "[단신]", "[간추린 뉴스]", "[간추린뉴스]", "[오늘의 단신]", "[게시판]", "지역소식]", "단신]"]
    if any(tag in new_title for tag in roundup_tags):
        return True

    clean_t1 = strip_title_prefix(new_title)
    norm_t1 = re.sub(r'[\W_]+', '', clean_t1)
    new_t_bi = get_bigrams(clean_t1)
    new_d_bi = get_bigrams(new_desc)
    new_dt = parse_yy_mm_dd(new_date)
    new_sig = extract_capture_recruit_signature(new_title, new_desc)
    
    for seen in seen_articles:
        clean_t2 = strip_title_prefix(seen["title"])
        norm_t2 = re.sub(r'[\W_]+', '', clean_t2)
        # 1. 완전 포함 관계
        if norm_t1 and norm_t2 and (norm_t1 in norm_t2 or norm_t2 in norm_t1):
            return True

        seen_dt = parse_yy_mm_dd(seen["date"])
        day_gap = abs((new_dt - seen_dt).days) if (new_dt and seen_dt) else (0 if seen["date"] == new_date else 99)

        # 2. 동일 지자체 포획단·피해방지단 모집/운영/교육 중복 보도 차단 (7일 이내)
        if new_sig and seen.get("sig") and new_sig == seen["sig"] and day_gap <= 7:
            return True

        # 3. 인접 날짜(3일 이내) 기사의 제목·요약 유사도 검사 (보도자료 복붙 차단)
        if day_gap <= 3:
            seen_t_bi = get_bigrams(clean_t2)
            seen_d_bi = get_bigrams(seen["desc"])
            
            if len(new_t_bi) > 0 and len(seen_t_bi) > 0:
                t_inter = len(new_t_bi.intersection(seen_t_bi))
                t_union = len(new_t_bi.union(seen_t_bi))
                if t_inter >= 6 or (t_union > 0 and t_inter / t_union >= 0.22):
                    return True
            
            if len(new_d_bi) > 0 and len(seen_d_bi) > 0:
                d_inter = len(new_d_bi.intersection(seen_d_bi))
                d_union = len(new_d_bi.union(seen_d_bi))
                if d_inter >= 12 or (d_union > 0 and d_inter / d_union >= 0.25):
                    return True
                    
    return False

def get_news(keyword, display=50):
    """네이버 뉴스 검색 API 호출"""
    encText = urllib.parse.quote(keyword)
    url = f"https://openapi.naver.com/v1/search/news.json?query={encText}&display={display}&sort=sim"
    
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    
    try:
        response = urllib.request.urlopen(request, timeout=5)
        rescode = response.getcode()
        if rescode == 200:
            response_body = response.read()
            return json.loads(response_body.decode('utf-8'))['items']
        else:
            print("API Error Code:" + str(rescode))
            return []
    except Exception as e:
        print(f"API 호출 중 오류 ({keyword}): {e}")
        return []

def main():
    if not client_id or not client_secret:
        print("네이버 API 인증 정보가 없습니다. (NAVER_CLIENT_ID, NAVER_CLIENT_SECRET 환경변수 확인)")
        return

    print("뉴스 데이터 업데이트 시작...")
    
    news_data_output: dict[str, list[dict[str, str | int]]] = {
        "hunting": [],
        "asf": [],
        "ai": [],
        "ecosystem": [],
        "association": [],
        "editorial": []
    }
    
    article_id = 1
    global_seen_articles = []
    global_seen_links = set()
    
    for category, keywords in categories.items():
        print(f"[{category}] 카테고리 수집 중...")
        
        for keyword in keywords:
            items = get_news(keyword, display=30)
            
            for item in items:
                if not isinstance(item, dict):
                    continue
                # 동일 응답 객체에서 제목·요약·링크 일관 추출 및 필수값 검증
                title = clean_html(str(item.get('title', '')))
                description = clean_html(str(item.get('description', '')))
                link = str(item.get('link', '')).strip()
                original_link = str(item.get('originallink', '')).strip()
                if not title or not link:
                    continue
                
                # 협회관련 필터
                if category == "association":
                    assoc_keywords = ["야생생물관리협회", "야생생물 관리협회", "관리협회", "밀렵감시단", "수렵면허"]
                    if not any(ak in title or ak in description for ak in assoc_keywords):
                        continue
                
                # 스팸/투자/해외 기사 차단
                blacklist = [
                    "중앙백신", "특징주", "주가", "주식", "증시", "상한가", "급등", "수혜주", "테마주", 
                    "이글벳", "제일바이오", "체시스", "대성미생물", "진바이오텍", "우진비앤지", "파루", 
                    "코미팜", "마니커", "하림", "투자", "매수", "매도", "종목", "코스닥", "코스피",
                    "남아프리카", "남아공", "케냐", "탄자니아", "짐바브웨", "사파리", 
                    "코뿔소", "코끼리", "사자", "표범", "기린", "밀매", "밀수", "해외 동물원",
                    "미국", "중국", "일본", "러시아", "호주", "캐나다", "유럽", "영국", "프랑스", "독일", "인도",
                    "목사", "교회", "예배", "기독교", "천주교", "불교", "스님", "사찰", "조계종", "신부", "수녀", "성당", "미사", "법회"
                ]
                if any(b_word in title for b_word in blacklist):
                    continue
                
                # 사설/기획 판별
                editorial_tags = ["[사설]", "[기획]", "[기고]", "[칼럼]", "사설]", "기고]", "칼럼]", "기획]"]
                is_editorial_by_tag = any(tag in title for tag in editorial_tags)
                
                if category == "editorial" or is_editorial_by_tag:
                    target_category = "editorial"
                else:
                    target_category = category
                
                # 생태계교란생물 노이즈 기사(내분비계 교란물질·환경호르몬·화장품 등) 제외
                if category == "ecosystem" or target_category == "ecosystem":
                    eco_text = title + " " + description
                    if any(ex_word in eco_text for ex_word in ECOSYSTEM_EXCLUDE_KEYWORDS):
                        continue
                
                # 카테고리별 엄격한 유효성 검사
                if target_category == "asf":
                    if "돼지열병" not in title and "asf" not in title.lower():
                        continue
                elif target_category == "ai":
                    if "인플루엔자" not in title and "ai" not in title.lower() and "조류독감" not in title:
                        continue
                elif target_category == "hunting":
                    if "돼지열병" in title or "asf" in title.lower():
                        continue
                elif target_category == "editorial":
                    good_tags = ["사설", "기획", "기고", "칼럼", "인터뷰", "시론", "데스크"]
                    if not any(tag in title for tag in good_tags):
                        continue
                    must_have = [
                        "야생동물", "수렵", "유해조수", "밀렵", "생태계교란", "동물보호", 
                        "철새", "돼지열병", "포획단", "가축전염병", "유해야생동물",
                        "asf", "아프리카돼지열병", "조류인플루엔자", "조류독감", "야생조류"
                    ]
                    comp_text = (title + " " + description).lower()
                    if not any(word in comp_text for word in must_have):
                        continue
                
                # 허용 기간 설정
                max_days = 7
                if target_category in ["association", "editorial"]:
                    max_days = 90
                elif target_category in ["ecosystem", "hunting"]:
                    max_days = 30
                    
                pub_date_str = str(item.get('pubDate', ''))
                days_diff = 0
                
                KST = timezone(timedelta(hours=9))
                now_kst = datetime.now(KST)
                formatted_date = now_kst.strftime("%y.%m.%d")
                
                try:
                    pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
                    pub_date_kst = pub_date.astimezone(KST)
                    days_diff = (now_kst.date() - pub_date_kst.date()).days
                    
                    if days_diff > max_days:
                        continue
                        
                    formatted_date = pub_date_kst.strftime("%y.%m.%d")
                except Exception:
                    pass
                
                if link in global_seen_links:
                    continue
                global_seen_links.add(link)

                if is_duplicate_article(title, description, formatted_date, global_seen_articles):
                    continue
                
                global_seen_articles.append({
                    "date": formatted_date,
                    "title": title,
                    "desc": description,
                    "sig": extract_capture_recruit_signature(title, description)
                })
                
                if len(news_data_output[target_category]) >= 12:
                    continue
                
                selected_image = get_best_image(target_category, title, description)
                excerpt = description[:95] + '...' if len(description) > 95 else description
                
                body_content = description
                source_name = extract_source_name(link, original_link)
                
                news_item = {
                    "id": article_id,
                    "title": title,
                    "excerpt": excerpt,
                    "body": body_content,
                    "source": source_name,
                    "image": selected_image,
                    "daysAgo": days_diff,
                    "date": formatted_date,
                    "link": link
                }
                
                news_data_output[target_category].append(news_item)
                article_id += 1
                
    for cat in news_data_output.keys():
        news_data_output[cat] = news_data_output[cat][:12]

    os.makedirs('data', exist_ok=True)
    output_path = os.path.join('data', 'newsData.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(news_data_output, f, ensure_ascii=False, indent=4)
        
    print(f"성공적으로 뉴스 데이터를 업데이트 했습니다. ({output_path})")

if __name__ == "__main__":
    main()
