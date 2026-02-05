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
    print("LOG: AI 분석 요청 중 (Gemini 2.5 Flash)...")
    
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GOOGLE_API_KEY}"
    
    # 🌟 프롬프트 수정: 가독성 좋은 '개조식' 스타일 강제
    prompt = f"""
    당신은 17년차 베테랑 정책 지원관이자 거시경제 분석가입니다.
    오늘의 뉴스를 바탕으로 핵심 내용을 브리핑해주세요.

    [작성 원칙]
    1. 줄글보다 **'개조식(Bullet points)'**을 사용하여 가독성을 높일 것.
    2. 각 항목은 구체적인 **'정책적 함의'**와 **'경제적 영향'**을 포함할 것.
    3. 텔레그램 전송을 위해 마크다운 기호(*, #) 대신 이모지(🔹, ▪️, 💡)를 적극 활용할 것.
    4. 문체는 정중하고 명확하게 ("~함", "~것으로 보임" 등).

    [뉴스 데이터]
    {full_content}

    [출력 양식]
    📅 {datetime.date.today()} Henry의 모닝 브리핑

    1. 🏛 정치/정책 동향
    🔹 (핵심 이슈 제목)
     ▪️ 내용: (요약)
     ▪️ 함의: (정책적 분석)

    2. 💰 경제/금융 흐름
    🔹 (핵심 이슈 제목)
     ▪️ 영향: (시장/투자 영향 분석)

    3. 🌍 국제 정세
    🔹 (핵심 이슈 제목)
     ▪️ 리스크: (지정학적 분석)

    💡 오늘의 인사이트: (전체 요약 한 문장)
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
    # parse_mode를 빼서 전송 에러를 원천 차단하되, 이모지로 가독성 확보
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, json=payload)

if __name__ == "__main__":
    briefing = get_news_summary()
    send_telegram_message(briefing)
