from google import genai
import json
import os
import sys
from datetime import datetime, timezone, timedelta

def load_news_data(filepath):
    """지정된 JSON 파일에서 뉴스 데이터를 로드합니다."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"뉴스 데이터를 읽는 데 실패했습니다: {e}")
        return None

def filter_weekly_news(news_data):
    """최근 7일 이내의 주요 뉴스만 필터링합니다."""
    weekly_news = {
        "hunting": [],
        "asf": [],
        "ai": [],
        "ecosystem": []
    }
    
    # KST 기준 현재 날짜
    # 뉴스 날짜 형식이 'YY.MM.DD' 이므로 문자열 파싱
    KST = timezone(timedelta(hours=9))
    now = datetime.now(KST).date()
    
    for category in weekly_news.keys():
        if category in news_data:
            for item in news_data[category]:
                try:
                    # '25.03.14' 형식 파싱
                    item_date = datetime.strptime(item['date'], "%y.%m.%d").date()
                    days_diff = (now - item_date).days
                    
                    # 최근 7일 이내의 기사만 추출
                    if 0 <= days_diff <= 7:
                        weekly_news[category].append(item)
                except Exception as e:
                    # 날짜 형식이 다를 경우를 대비한 대체 로직: API 제공 daysAgo 값 활용
                    if 'daysAgo' in item and item['daysAgo'] <= 7:
                         weekly_news[category].append(item)
                    
    return weekly_news

def generate_weekly_briefing(weekly_news):
    """Gemini API를 사용하여 주간 브리핑 텍스트를 생성합니다."""
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY 환경 변수가 설정되어 있지 않습니다.")
        sys.exit(1)
        
    client = genai.Client(api_key=api_key)
    
    # 결제 계정이 연동되었으므로, 최신 모델인 2.0-flash를 정상적으로 사용할 수 있습니다.
    model_name = 'gemini-2.0-flash'
    
    # 이번 주 차수 계산 (예: 3월 2주차)
    now = datetime.now()
    month = now.month
    # 해당 월의 몇 번째 주인지 대략적 계산 (1~4주)
    week_num = (now.day - 1) // 7 + 1
    
    date_header = f"🚨 {month}월 {week_num}주차 야생생물 관련 주요 동향 🚨\n\n"
    
    # 프롬프트에 제공할 데이터 문자열 구성
    data_str = "다음은 최근 1주일 동안 수집된 카테고리별 주요 뉴스 원문(제목과 요약)입니다:\n\n"
    for cat, items in weekly_news.items():
        data_str += f"[{cat.upper()}]\n"
        for item in items[:5]: # 카테고리당 너무 많은 데이터가 들어가면 환각 가능성이 있으므로 상위 5개로 제한
            data_str += f"- 제목: {item['title']}\n"
            data_str += f"- 요약: {item['excerpt']}\n"
        data_str += "\n"
        
    prompt = f"""
    너는 야생생물관리협회(야생동물 포획, 생태계 교란종 관리, 아프리카돼지열병 및 조류인플루엔자 예방 등을 담당)의 전문 분석가이자 보고서 작성자야.
    
    다음 뉴스 데이터를 분석해서, 회원들에게 보내줄 '주간 뉴스 브리핑' 봇 메시지를 작성해줘.
    
    [데이터]
    {data_str}
    
    [출력 양식 규칙]
    1. 다음의 구조를 정확히 지켜서 마크다운 없이 순수 텍스트(강조를 위한 별표 **등은 허용)로 작성해 줘.
    2. 뉴스 원문의 내용만을 바탕으로 요약해 줘.
    3. 각 섹션마다 뉴스가 1~2줄의 간결한 개조식 문장으로 요약되어야 해.
    4. 관련 뉴스가 전혀 없는 섹션은 "관련 특이동향 없음" 이라고 적어줘.
    
    [출력 포맷 예시]
    {date_header}

    1. 야생동물 질병(ASF, AI) 현황
    - [이곳에 요약 내용 작성]
    
    2. 수렵 및 포획단 동향
    - [이곳에 요약 내용 작성]
    
    3. 생태계교란생물 소식
    - [이곳에 요약 내용 작성]
    
    _※ 본 요약은 네이버 뉴스 검색 결과를 바탕으로 제미나이가 주간 단위로 분석하여 제공하는 브리핑입니다._
    """
    
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        return response.text
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Gemini API 호출 중 오류 발생: {e}")
        return None

def save_briefing(text, output_filepath):
    """생성된 브리핑 텍스트를 파일로 저장합니다."""
    try:
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"주간 브리핑이 성공적으로 생성되었습니다: {output_filepath}")
        return True
    except Exception as e:
        print(f"파일 저장 중 오류 발생: {e}")
        return False

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_filepath = os.path.join(base_dir, 'data', 'newsData.json')
    output_filepath = os.path.join(base_dir, 'data', 'weekly_briefing.txt')
    
    # 1. 뉴스 데이터 로드
    news_data = load_news_data(data_filepath)
    if not news_data:
        return
        
    # 2. 최근 일주일치 뉴스 필터링
    weekly_news = filter_weekly_news(news_data)
    
    # 필터링된 뉴스가 하나도 없는지 확인
    total_news = sum(len(items) for items in weekly_news.values())
    if total_news == 0:
        print("최근 일주일 내의 뉴스가 없어 브리핑을 생성할 수 없습니다.")
        return
        
    print(f"최근 7일간의 뉴스 총 {total_news}건 분석 중...")
    
    # 3. 브리핑 생성 (Gemini API)
    briefing_text = generate_weekly_briefing(weekly_news)
    
    if briefing_text:
        # 4. 파일 저장
        save_briefing(briefing_text, output_filepath)

if __name__ == "__main__":
    main()
