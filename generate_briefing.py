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

def filter_weekly_news(news_data, max_days=7):
    """최근 지정된 일수(기본 7일) 이내의 주요 뉴스만 필터링합니다."""
    weekly_news = {
        "hunting": [],
        "asf": [],
        "ai": [],
        "ecosystem": [],
        "association": [],
        "editorial": []
    }
    
    # KST 기준 현재 날짜
    KST = timezone(timedelta(hours=9))
    now = datetime.now(KST).date()
    
    for category in weekly_news.keys():
        if category in news_data:
            for item in news_data[category]:
                try:
                    # 'YY.MM.DD' 형식 파싱 (예: 26.08.15)
                    item_date = datetime.strptime(item['date'], "%y.%m.%d").date()
                    days_diff = (now - item_date).days
                    
                    if 0 <= days_diff <= max_days:
                        weekly_news[category].append(item)
                except Exception:
                    if 'daysAgo' in item and item['daysAgo'] <= max_days:
                        weekly_news[category].append(item)
                        
    return weekly_news

def generate_weekly_briefing(weekly_news):
    """Gemini API를 사용하여 주간 브리핑 텍스트를 생성합니다."""
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY 환경 변수가 설정되어 있지 않습니다.")
        sys.exit(1)
        
    client = genai.Client(api_key=api_key)
    
    # 환경변수로 모델을 지정할 수 있으며 기본값은 최신 고성능 모델 사용
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    
    KST = timezone(timedelta(hours=9))
    now = datetime.now(KST)
    month = now.month
    # 해당 월의 몇 번째 주인지 계산 (1~5주)
    week_num = (now.day - 1) // 7 + 1
    
    date_header = f"🚨 {month}월 {week_num}주차 야생생물 & 수렵행정 종합 브리핑 🚨"
    
    # 프롬프트에 제공할 데이터 문자열 구성
    data_str = ""
    category_labels = {
        "hunting": "수렵 및 포획단",
        "asf": "ASF (아프리카돼지열병)",
        "ai": "AI (조류인플루엔자)",
        "ecosystem": "생태계교란생물",
        "association": "협회 및 유관기관",
        "editorial": "사설 및 기획보도"
    }
    
    for cat, label in category_labels.items():
        items = weekly_news.get(cat, [])
        if items:
            data_str += f"[{label}]\n"
            for item in items[:6]:
                data_str += f"- 제목: {item['title']}\n"
                data_str += f"  요약: {item['excerpt']}\n"
            data_str += "\n"
        
    prompt = f"""
    너는 야생생물관리협회(야생동물 포획, 생태계 교란종 관리, 아프리카돼지열병 및 조류인플루엔자 예방 등을 담당)의 수석 전문 분석관이야.
    
    다음 뉴스 데이터를 분석해서, 회원 및 지자체 담당자들에게 전달할 전문적이고 실용적인 '주간 업무 브리핑' 메시지를 작성해줘.
    
    [데이터]
    {data_str}
    
    [출력 양식 규칙]
    1. 다음의 헤더와 목차 구조를 정확히 지켜서 작성해 줘. (강조를 위한 볼드체 **텍스트** 적극 활용)
    2. 뉴스 원문의 사실에 기반하여 핵심만 간결한 개조식(- 문장)으로 요약해 줘.
    3. 실무자(지자체 공무원, 협회원, 포획단원)가 주의해야 할 현장 시사점 및 권고사항을 마지막에 1~2줄로 포함해줘.
    4. 관련 뉴스가 전혀 없는 섹션은 "관련 특이동향 없음" 이라고 명시해줘.
    
    [출력 포맷 예시]
    {date_header}

    1. 🐗 야생동물 질병 (ASF · AI) 동향
    - [ASF/AI 관련 핵심 요약]
    
    2. 🎯 수렵 · 포획단 및 총기 안전
    - [수렵/포획단/총기안전 관련 핵심 요약]
    
    3. 🌿 생태계교란생물 및 환경보전
    - [교란종 퇴치/외래생물 관련 핵심 요약]

    4. 📢 현장 실무 및 안전 권고사항
    - [현장 요원 및 지자체 담당자를 위한 핵심 행동 요령 및 주의사항 1~2개]
    
    _※ 본 브리핑은 야생생물관리협회 뉴스레이더 수집 데이터를 바탕으로 Gemini AI가 주간 단위로 종합 분석한 보고서입니다._
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
        print(f"Gemini API ({model_name}) 호출 중 오류 발생: {e}")
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
        
    # 2. 최근 7일치 뉴스 필터링 (부족할 경우 최대 30일치로 확장)
    weekly_news = filter_weekly_news(news_data, max_days=7)
    total_news = sum(len(items) for items in weekly_news.values())
    
    if total_news < 3:
        print("최근 7일치 뉴스가 부족하여 30일치 기사로 범위를 확장하여 분석합니다.")
        weekly_news = filter_weekly_news(news_data, max_days=30)
        total_news = sum(len(items) for items in weekly_news.values())
        
    if total_news == 0:
        print("수집된 유효 뉴스가 없어 브리핑을 생성할 수 없습니다.")
        return
        
    print(f"분석 대상 뉴스 총 {total_news}건 분석 중...")
    
    # 3. 브리핑 생성 (Gemini API)
    briefing_text = generate_weekly_briefing(weekly_news)
    
    if briefing_text:
        # 4. 파일 저장
        save_briefing(briefing_text, output_filepath)

if __name__ == "__main__":
    main()
