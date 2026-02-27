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
    "ecosystem": ["images/env_gov.png", "images/nutria.png", "images/bullfrog.png", "images/hunter.png"]
}

def clean_html(raw_html):
    """HTML 태그 제거 및 특수문자 변환"""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    cleantext = cleantext.replace('&quot;', '"').replace('&apos;', "'").replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    return cleantext

def get_news(keyword, display=3):
    """네이버 뉴스 검색 API 호출"""
    encText = urllib.parse.quote(keyword)
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
        "ecosystem": []
    }
    
    article_id: int = 1
    
    for category, keywords in categories.items():
        print(f"[{category}] 카테고리 수집 중...")
        for idx, keyword in enumerate(keywords):
            # 카테고리별로 키워드당 2개씩 가져와서 총 6~8개 구성
            items = get_news(keyword, display=2)
            
            for item in items: # type: ignore
                if not isinstance(item, dict):
                    continue
                title = clean_html(str(item.get('title', '')))
                description = clean_html(str(item.get('description', '')))
                link = str(item.get('link', ''))
                
                # 이미지 로테이션 선택
                img_list = image_mapping[category]
                selected_image = img_list[idx % len(img_list)]
                
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
                
                news_data_output[category].append(news_item)
                article_id += 1

    # data 폴더 확인 및 생성
    os.makedirs('data', exist_ok=True)
    
    # JSON 파일로 저장
    output_path = os.path.join('data', 'newsData.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(news_data_output, f, ensure_ascii=False, indent=4)
        
    print(f"성공적으로 뉴스 데이터를 업데이트 했습니다. ({output_path})")

if __name__ == "__main__":
    main()
