import feedparser
import requests
import os
import datetime
import json
import sys

# 1. 환경변수 설정
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

RSS_FEEDS = {
    "🏛 국내 정치": "https://www.yna.co.kr/rss/politics.xml",
    "💰 경제/금융": "https://www.mk.co.kr/rss/30000001/",
    "🌍 국제 정세": "http://feeds.bbci.co.uk/news/world/rss.xml",
}

def get_news_summary():
    # [뉴스 수집]
    full_content = ""
    print("LOG: 뉴스 수집 중...")
    for category, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            full_content += f"\n[{category}]\n"
            for entry in feed.entries[:3]:
                full_content += f"- {entry.title}\n"
        except Exception as e:
            print(f"LOG: {category} 수집 실패: {e}")

    # [AI 분석 요청]
    print("LOG: AI 분석 요청 중 (High-End Model: Gemini 2.5 Pro)...")
    
    # 🌟 Henry님의 선택: 깊이 있는 분석을 위해 'gemini-2.5-pro' 사용
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-pro:generateContent?key={GOOGLE_API_KEY}"
    
    prompt = f"""
    당신은 17년차 베테랑 정책 지원관이자 거시경제 분석가입니다.
    아래 수집된 뉴스 헤드라인들을 종합적으로 분석하여 브리핑해 주세요.

    [분석 요구사항]
    1. 단순 요약이 아닌, **'이면의 함의(Implication)'**를 도출할 것.
    2. 정치 이슈가 경제(시장, 금리, 기업)에 미칠 영향을 논리적으로 연결할 것.
    3. 문체는 전문적이고 건조한 보고서 스타일(개조식)을 유지할 것.
    4. **특수문자(*, #)는 사용 금지.** (순수 텍스트로 작성)

    [뉴스 데이터]
    {full_content}

    [출력 양식]
    📅 {datetime.date.today()} Henry의 심층 브리핑

    1. 🏛 정책 및 정치 지형
    - (핵심 사안과 그로 인한 파장 분석)

    2. 💰 경제 및 시장 전망
    - (주요 변수 및 투자 시장 영향)

    3. 🌍 글로벌 리스크 체크
    - (국제 정세가 국내에 미칠 영향)

    💡 오늘의 인사이트: (전체 흐름을 관통하는 한 문장)
    """

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        data = response.json()
        
        if "candidates" in data:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            print(f"LOG: 응답 실패 내용: {data}")
            return f"🚨 분석 실패: {data}"

    except Exception as e:
        return f"통신 에러: {str(e)}"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, json=payload)

if __name__ == "__main__":
    briefing = get_news_summary()
    send_telegram_message(briefing)
