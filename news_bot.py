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
            # 상위 3개 기사 수집
            for index, entry in enumerate(feed.entries[:3], 1):
                full_content += f"{index}. {entry.title}\n"
        except Exception as e:
            print(f"LOG: {category} 수집 실패: {e}")

    # [AI 분석 요청]
    print("LOG: AI 분석 요청 중 (Gemini 2.5 Flash)...")
    
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GOOGLE_API_KEY}"
    
    # 🌟 프롬프트 대폭 수정: '3가지 꼭지' 강제 출력 명령 추가
    prompt = f"""
    당신은 17년차 베테랑 정책 지원관이자 거시경제 분석가입니다.
    수집된 뉴스 데이터를 바탕으로 오늘 아침 브리핑을 작성하세요.

    [작성 원칙]
    1. **수량 엄수:** 각 카테고리(정치, 경제, 국제)별로 **반드시 3개의 기사를 각각 분리**하여 브리핑할 것. (절대 뭉뚱그리지 말 것)
    2. **구조:** 각 기사마다 '핵심 내용'과 Henry님을 위한 '정책/경제적 함의'를 포함할 것.
    3. **가독성:** 텔레그램 전송을 위해 마크다운 기호(*, #) 대신 이모지(🔹, 🔸)를 사용할 것.
    4. **형식:** 아래 [출력 양식]을 정확히 따를 것.

    [뉴스 데이터]
    {full_content}

    [출력 양식]
    📅 {datetime.date.today()} Henry의 모닝 브리핑

    1. 🏛 정치/정책 (3건)
    🔹 (기사 1 제목)
     🔸 내용: (요약)
     🔸 함의: (정책적 시사점)
    
    🔹 (기사 2 제목)
     🔸 내용: (요약)
     🔸 함의: (분석)

    🔹 (기사 3 제목)
     🔸 내용: (요약)
     🔸 함의: (분석)

    2. 💰 경제/금융 (3건)
    🔹 (기사 1 제목)
     🔸 영향: (시장/투자 영향)

    🔹 (기사 2 제목)
     🔸 영향: (시장/투자 영향)

    🔹 (기사 3 제목)
     🔸 영향: (시장/투자 영향)

    3. 🌍 국제 정세 (3건)
    🔹 (기사 1 제목)
     🔸 리스크: (지정학적 분석)

    🔹 (기사 2 제목)
     🔸 리스크: (분석)

    🔹 (기사 3 제목)
     🔸 리스크: (분석)

    💡 오늘의 인사이트: (전체 관통 한 줄 요약)
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
            print(f"LOG: 응답 실패: {data}")
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
