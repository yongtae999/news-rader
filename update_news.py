import urllib.request
import urllib.parse
import json
import os
from datetime import datetime, timezone, timedelta
import re

# 네이버 API 인증 정보 (GitHub Secrets에서 가져옴)
client_id = os.environ.get("NAVER_CLIENT_ID", "")
client_secret = os.environ.get("NAVER_CLIENT_SECRET", "")

# 검색 키워드 및 카테고리 매핑
categories = {
    # 수렵 탭: 확실히 포획, 엽사, 총기안전 등과 관련된 단어로 좁힘
    "hunting": ["유해조수 포획단", "수렵면허", "총기 안전 수렵", "야생동물 포획"],
    # ASF 탭: 유해동물 포획이 아니라 '돼지열병' 자체가 강조되어야 함
    "asf": ["아프리카돼지열병 멧돼지", "ASF 멧돼지", "야생멧돼지 아프리카돼지열병"],
    # AI 탭: 야생조류 AI
    "ai": ["야생조류 조류인플루엔자", "고병원성 AI 야생조류", "철새 조류인플루엔자"],
    # 생태계 탭: 뉴트리아, 가시박, 교란종 등
    "ecosystem": ["생태계교란 교란종", "뉴트리아 포획", "황소개구리 퇴치", "가시박 제거"],
    "association": ["야생생물관리협회"]
}

# 뉴스 이미지 매핑 (랜덤 방지를 위해 카테고리별로 고정 이미지 지정)
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
    return cleantext

def get_best_image(category, title, description):
    """기사 제목과 내용을 분석하여 가장 적합한 이미지를 반환합니다."""
    combined_text = title + " " + description
    
    # 1. 특정 키워드에 대한 강력한 매칭
    if "경찰" in combined_text or "순찰" in combined_text or "단속" in combined_text or "총기" in combined_text:
        return "images/police.png"
    if "조류독감" in combined_text or "조류인플루엔자" in combined_text or "고병원성 AI" in combined_text.upper() or "철새" in combined_text or "야생조류" in combined_text:
        return "images/bird_flu.png"
    if "멧돼지" in combined_text or "돼지열병" in combined_text or "ASF" in combined_text.upper():
        return "images/boar.png"
    if "뉴트리아" in combined_text or "괴물쥐" in combined_text:
        return "images/nutria.png"
    if "개구리" in combined_text or "거북" in combined_text or "배스" in combined_text or "블루길" in combined_text:
        return "images/bullfrog.png"
    if "수렵" in combined_text or "엽사" in combined_text or "포획단" in combined_text or "사냥" in combined_text:
        return "images/hunter.png"
    if "환경부" in combined_text or "정부" in combined_text or "지자체" in combined_text or "환경청" in combined_text:
        return "images/env_gov.png"
        
    # 2. 매칭되는 키워드가 없을 경우 카테고리에 따른 기본(Fallback) 이미지 제공
    if category == "hunting":
        return "images/hunter.png"
    elif category == "asf":
        return "images/boar.png"
    elif category == "ai":
        return "images/bird_flu.png"
    elif category == "ecosystem":
        return "images/env_gov.png"
    elif category == "association":
        return "images/env_gov.png"
    elif category == "editorial":
        return "images/env_gov.png"
        
    return "images/env_gov.png"

def longest_common_substring(s1, s2):
    """두 문자열 사이의 가장 긴 연속된 공통 부분 문자열의 길이를 반환"""
    m = [[0] * (1 + len(s2)) for _ in range(1 + len(s1))]
    longest, x_longest = 0, 0
    for x in range(1, 1 + len(s1)):
        for y in range(1, 1 + len(s2)):
            if s1[x - 1] == s2[y - 1]:
                m[x][y] = m[x - 1][y - 1] + 1
                if m[x][y] > longest:
                    longest = m[x][y]
                    x_longest = x
            else:
                m[x][y] = 0
    return longest

def get_news(keyword, display=3):
    """네이버 뉴스 검색 API 호출"""
    encText = urllib.parse.quote(keyword)
    # sort=sim(정확도순)으로 복구하여, 동시간대 복붙 기사 중복을 줄이고 품질 높은 기사를 우선 확보
    url = f"https://openapi.naver.com/v1/search/news.json?query={encText}&display={display}&sort=sim"
    
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    
    try:
        response = urllib.request.urlopen(request)
        rescode = response.getcode()
        if rescode == 200:
            response_body = response.read()
            return json.loads(response_body.decode('utf-8'))['items']
        else:
            print("Error Code:" + str(rescode))
            return []
    except Exception as e:
        print(f"API 호출 중 오류 발생: {e}")
        return []

def main():
    if not client_id or not client_secret:
        print("네이버 API 인증 정보가 없습니다. (환경변수 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET 확인 요망)")
        return

    print("뉴스 데이터 업데이트 시작...")
    
    news_data_output: dict[str, list[dict[str, str | int]]] = {
        "hunting": [],
        "asf": [],
        "ai": [],
        "ecosystem": [],
        "association": [], # 6번째 협회관련 탭용 메모리
        "editorial": [] # 사설/기획기사는 따로 담을 빈 바구니 준비
    }
    
    article_id: int = 1
    
    # 전체 카테고리 통합 중복 기사 필터링용 Set (동일 기사가 여러 탭에 뜨는 것 방지)
    global_seen_titles = set()
    global_seen_links = set()
    
    for category, keywords in categories.items():
        print(f"[{category}] 카테고리 수집 중...")
        
        for idx, keyword in enumerate(keywords):
            # API 기사 수집량을 최대치(100개)로 가져와서 필터링
            display_count = 100
            items = get_news(keyword, display=display_count)
            
            for item in items: # type: ignore
                if not isinstance(item, dict):
                    continue
                title = clean_html(str(item.get('title', '')))
                description = clean_html(str(item.get('description', '')))
                
                # 협회관련 탭의 경우 반드시 "야생생물관리협회" 단어가 포함되어야 함
                if category == "association":
                    if "야생생물관리협회" not in title and "야생생물관리협회" not in description:
                        continue
                
                # 스팸/테마주/해외 기사 원천 차단 블랙리스트
                blacklist = [
                    # 주식/투자 관련
                    "중앙백신", "특징주", "주가", "주식", "증시", "상한가", "급등", "수혜주", "테마주", 
                    "이글벳", "제일바이오", "체시스", "대성미생물", "진바이오텍", "우진비앤지", "파루", 
                    "코미팜", "마니커", "하림", "투자", "매수", "매도", "종목", "코스닥", "코스피",
                    # 아프리카나 해외 사파리, 밀수 관련 차단
                    "남아프리카", "남아공", "케냐", "탄자니아", "짐바브웨", "사파리", 
                    "코뿔소", "코끼리", "사자", "표범", "기린", "밀매", "밀수", "해외 동물원", "국제"
                ]
                if any(b_word in title for b_word in blacklist):
                    continue
                
                # 카테고리별 엄격한 필수 단어 확인 (오분류 방지)
                if category == "asf":
                    # ASF 카테고리는 제목에 반드시 'ASF' 나 '돼지열병'이 있어야 통과 (본문에만 있는 단순 포획기사 배제)
                    if "돼지열병" not in title and "asf" not in title.lower():
                        continue
                elif category == "ai":
                    # AI 카테고리도 제목 중심으로 판별
                    if "인플루엔자" not in title and "ai" not in title.lower() and "조류독감" not in title:
                        continue
                elif category == "hunting":
                    # 아프리카돼지열병 위주 기사가 수렵으로 빠지는 것을 방지 (제목 기준)
                    if "돼지열병" in title or "asf" in title.lower():
                        continue
                
                # 2024년, 2025년 초 등 과거 기사 원천 차단 (최근 7일 이내 기사만 허용)
                pub_date_str = str(item.get('pubDate', ''))
                days_diff = 0
                
                # 한국 시간(KST) 기준 설정
                KST = timezone(timedelta(hours=9))
                now_kst = datetime.now(KST)
                formatted_date = now_kst.strftime("%y.%m.%d")
                
                try:
                    # 네이버 API 날짜 형식: Tue, 04 Mar 2025 14:02:00 +0900
                    pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
                    
                    # 기사 발행 시간을 KST로 변환
                    pub_date_kst = pub_date.astimezone(KST)
                    
                    # 날짜 차이 계산 (KST 기준)
                    days_diff = (now_kst.date() - pub_date_kst.date()).days
                    
                    if days_diff > 7:
                        continue # 7일 이상 지난 과거 기사 스킵
                        
                    # YY.MM.DD 형식으로 포맷팅 (KST 기준)
                    formatted_date = pub_date_kst.strftime("%y.%m.%d")
                except Exception as e:
                    # 날짜 형식이 이상하면 기본값(오늘)으로 설정 후 통과 (API 오류 방지)
                    print(f"날짜 파싱 오류: {e} - {pub_date_str}")
                    pass
                
                link = str(item.get('link', ''))
                
                # 링크 중복 검사 (완전히 동일한 기사가 다른 키워드로 수집된 경우 즉시 차단)
                if link in global_seen_links:
                    continue
                global_seen_links.add(link)

                # 특수문자 및 공백을 모두 제거한 핵심 문자열 추출 (제목 중복 제거용)
                norm_title = re.sub(r'[\W_]+', '', title)
                
                is_duplicate = False
                for seen_title in global_seen_titles:
                    # 1. 완전 포함 관계
                    if norm_title in seen_title or seen_title in norm_title:
                        is_duplicate = True
                        break
                    # 2. 가장 긴 연속 공통 문자열이 8글자 이상 겹치면 (유사 기사로 간주, 기존 10글자에서 기준 강화)
                    if longest_common_substring(norm_title, seen_title) >= 8:
                        is_duplicate = True
                        break
                        
                if is_duplicate:
                    continue
                global_seen_titles.add(norm_title)
                
                # [사설], [기획], [기고], [칼럼] 등이 제목에 있으면 "사설/기획" 탭으로 강제 이동
                editorial_tags = ["[사설]", "[기획]", "[기고]", "[칼럼]", "사설]", "기고]", "칼럼]", "기획]"]
                target_category = category
                
                if any(tag in title for tag in editorial_tags):
                    target_category = "editorial"
                    # 만약 사설 탭이 이미 10개가 찼다면 더 넣지 않고 무시
                    if len(news_data_output["editorial"]) >= 10:
                        continue
                else:
                    # 일반 기사인데 이미 해당 카테고리가 10개가 찼다면 스킵
                    if len(news_data_output[category]) >= 10:
                        continue
                
                link = str(item.get('link', ''))
                
                # 기사 내용을 바탕으로 가장 적절한 스마트 이미지 선택
                selected_image = get_best_image(category, title, description)
                
                # 요약문 생성 (description이 너무 길면 자름)
                excerpt = description[:80] + '...' if len(description) > 80 else description
                
                # 본문(모달용) - API에서 본문을 다 주진 않으므로 description 활용에 링크 추가
                body_content = f"네이버 뉴스 검색 결과입니다.<br><br>{description}<br><br><a href='{link}' target='_blank' style='color:#3a86ff; text-decoration:underline;'>원문 기사 보러가기</a>"
                
                news_item = {
                    "id": article_id,
                    "title": title,
                    "excerpt": excerpt,
                    "body": body_content,
                    "source": "네이버 뉴스",
                    "image": selected_image,
                    "daysAgo": days_diff,
                    "date": formatted_date,
                    "link": link
                }
                
                # 강제로 할당된 target_category("editorial" 또는 원본)에 저장
                news_data_output[target_category].append(news_item)
                article_id += 1
                
    # 카테고리별로 혹시 넘치면 10개만 정확히 잘라내서 저장 (위에서 걸렀지만 한 번 더 안전장치)
    for cat in news_data_output.keys():
        news_data_output[cat] = news_data_output[cat][:10]

    # data 폴더 확인 및 생성
    os.makedirs('data', exist_ok=True)
    
    # JSON 파일로 저장
    output_path = os.path.join('data', 'newsData.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(news_data_output, f, ensure_ascii=False, indent=4)
        
    print(f"성공적으로 뉴스 데이터를 업데이트 했습니다. ({output_path})")

if __name__ == "__main__":
    main()
