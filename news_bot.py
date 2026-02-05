import feedparser
import requests
import os
import datetime
import json
import sys

# 1. 환경변수 가져오기
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# 2. 뉴스 소스 설정
RSS_FEEDS = {
    "🏛 국내 정치/정책": "https://www.yna.co.kr/rss/politics.xml",
    "💰 경제/금융": "https://www.mk.co.kr/rss/30000001/",
    "🌍 국제 정세": "http://feeds.bbci.co.uk/news/world/rss.xml",
}

def get_news_summary():
    # [뉴스 수집]
    full_content = ""
    print("LOG: 뉴스 데이터 수집 중...")
    for category, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            full_content += f"\n[{category}]\n"
            for entry in feed.entries[:3]: # 카테고리별 3개씩
                full_content += f"- {entry.title}\n"
        except Exception as e:
            print(f"LOG: {category} 수집 실패 - {e}")

    # [AI 분석] - 여기가 핵심 변경점입니다!
    print("LOG: Gemini Pro 모델에게 분석 요청 중...")
    
    # 🌟 변경점: gemini-1.5-flash -> gemini-pro (표준 모델 사용)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GOOGLE_API_KEY}"
    
    prompt = f"""
    당신은 17년차 정책 지원관이자 거시경제 전문가입니다.
    아래 뉴스들을 읽고 '정책적 시사점'과 '경제적 영향'을 중심으로 브리핑해주세요.
    **주의: 특수문자나 마크다운 없이 순수 텍스트로만 작성하세요.**

    [뉴스 데이터]
    {full_content}

    [출력 양식]
    📅 {datetime.date.today()} Henry의 모닝 브리핑

    1. 정치/정책 이슈
    (내용)

    2. 경제/금융 흐름
    (내용)

    3. 국제 정세
    (내용)

    💡 한 줄 인사이트: (내용)
    """

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        # 도구 없이 직접 요청 (requests 사용)
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        data = response.json()
        
        if "candidates" in data:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            print(f"LOG: AI 응답 에러 내용: {data}")
            return "죄송합니다. AI가 응답하지 않았습니다."

    except Exception as e:
        return f"통신 에러: {str(e)}"

def send_telegram_message(message):
    print("LOG: 텔레그램 전송 중...")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": message
        # parse_mode 제거 (전송 성공률 100% 보장)
    }
    res = requests.post(url, json=payload)
    if res.status_code == 200:
        print("LOG: ✅ 전송 성공! 핸드폰을 확인하세요.")
    else:
        print(f"LOG: ❌ 전송 실패: {res.text}")
        sys.exit(1)

if __name__ == "__main__":
    briefing = get_news_summary()
    send_telegram_message(briefing)
