import urllib.request
import urllib.parse
import json
import os
from datetime import datetime
import re

# 네이버 API 인증 정보 (GitHub Secrets에서 가져옴)
client_id = os.environ.get("NAVER_CLIENT_ID", "")
client_secret = os.environ.get("NAVER_CLIENT_SECRET", "")

# 검색 키워드 및 카테고리 매핑
categories = {
    "hunting": ["수렵 유해조수", "야생동물 밀렵 단속", "총기 안전 수렵"],
    "asf": ["아프리카돼지열병 멧돼지", "ASF 방역 멧돼지"],
    "ecosystem": ["생태계교란생물", "뉴트리아 포획", "황소개구리 퇴치", "가시박 제거"]
}

# 뉴스 이미지 매핑 (랜덤 방지를 위해 카테고리별로 고정 이미지 지정)
image_mapping = {
    "hunting": ["images/env_gov.png", "images/hunter.png", "images/police.png"],
    "asf": ["images/boar.png", "images/env_gov.png", "images/hunter.png"],
    "ecosystem": ["images/env_gov.png", "images/nutria.png", "images/bullfrog.png", "images/hunter.png"],
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
    elif category == "ecosystem":
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
    # sort=sim(정확도순) 대신 sort=date(최신순)을 사용하여 항상 최근 기사만 가져오도록 수정
    url = f"https://openapi.naver.com/v1/search/news.json?query={encText}&display={display}&sort=date"
    
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
        "ecosystem": [],
        "editorial": [] # 사설/기획기사는 따로 담을 빈 바구니 준비
    }
    
    article_id: int = 1
    
    for category, keywords in categories.items():
        print(f"[{category}] 카테고리 수집 중...")
        seen_titles = set() # 중복 기사 필터링용 Set
        
        for idx, keyword in enumerate(keywords):
            # 강력한 중복/스팸/날짜 제거를 감안하여 API 기사를 아주 넉넉하게 가져옴 (키워드당 15~20개)
            display_count = 20 if len(keywords) <= 2 else (15 if len(keywords) == 3 else 12)
            items = get_news(keyword, display=display_count)
            
            for item in items: # type: ignore
                if not isinstance(item, dict):
                    continue
                title = clean_html(str(item.get('title', '')))
                
                # 스팸/테마주 기사 원천 차단 블랙리스트 (제약사, 주식 용어 대폭 추가)
                blacklist = [
                    "중앙백신", "특징주", "주가", "주식", "증시", "상한가", "급등", "수혜주", "테마주", 
                    "이글벳", "제일바이오", "체시스", "대성미생물", "진바이오텍", "우진비앤지", "파루", 
                    "코미팜", "마니커", "하림", "투자", "매수", "매도", "종목", "코스닥", "코스피"
                ]
                if any(b_word in title for b_word in blacklist):
                    continue
                
                # 2024년, 2025년 초 등 과거 기사 원천 차단 (최근 7일 이내 기사만 허용)
                pub_date_str = str(item.get('pubDate', ''))
                try:
                    # 네이버 API 날짜 형식: Tue, 04 Mar 2025 14:02:00 +0900
                    pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
                    # 현재 시간(UTC)을 기준으로 Naver 시간대를 고려한 단순 날짜 차이 계산
                    days_diff = (datetime.now(pub_date.tzinfo) - pub_date).days
                    if days_diff > 7:
                        continue # 7일 이상 지난 과거 기사 스킵
                except Exception:
                    # 날짜 형식이 이상하면 일단 통과 (API 오류 방지)
                    pass
                
                # 특수문자 및 공백을 모두 제거한 핵심 문자열 추출 (중복 제거용)
                norm_title = re.sub(r'[\W_]+', '', title)
                
                is_duplicate = False
                for seen_title in seen_titles:
                    # 1. 완전 포함 관계
                    if norm_title in seen_title or seen_title in norm_title:
                        is_duplicate = True
                        break
                    # 2. 가장 긴 연속 공통 문자열이 10글자 이상 겹치면 (동일 사건 기사로 간주)
                    # (특수문자/공백 제거 상태이므로 10글자면 보통 3~5어절 길이의 핵심 문장 단위임)
                    if longest_common_substring(norm_title, seen_title) >= 10:
                        is_duplicate = True
                        break
                        
                if is_duplicate:
                    continue
                seen_titles.add(norm_title)
                
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
                
                description = clean_html(str(item.get('description', '')))
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
                    "daysAgo": 0, # 오늘 크롤링했으므로 항상 0 (NEW 딱지 붙음)
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
