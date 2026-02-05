import feedparser
import requests
import os
import datetime
import json
import sys

# --- 설정값 ---
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

RSS_FEEDS = {
    "🏛 국내 정치/정책": "https://www.yna.co.kr/rss/politics.xml",
    "💰 경제/금융": "https://www.mk.co.kr/rss/30000001/",
    "🌍 국제 정세 (BBC)": "http://feeds.bbci.co.uk/news/world/rss.xml",
}

def get_news_summary():
    full_content = ""
    print("LOG: 뉴스 수집 시작...")
    for category, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            full_content += f"\n[{category}]\n"
            for entry in feed.entries[:3]:
                full_content += f"- {entry.title}\n"
        except Exception as e:
            print(f"LOG: {category} 수집 에러 - {e}")

    print("LOG: AI 분석 요청 중...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GOOGLE_API_KEY}"
    
    prompt = f"""
    당신은 17년차 정책 지원관이자 거시경제 전문가입니다.
    아래 뉴스 헤드라인을 보고 '정책적 함의'와 '경제적 영향'을 중심으로 브리핑해 주세요.
    특수문자(*, #, _)는 사용하지 말고 일반 텍스트로만 작성해주세요.
    
    [뉴스 내용]
    {full_content}
    
    [출력 양식]
    📅 {datetime.date.today()} Henry의 모닝 브리핑
    
    1. 정치/정책 핵심
    (내용)
    
    2. 경제/금융 흐름
    (내용)
    
    3. 국제 이슈
    (내용)
    
    💡 한 줄 인사이트: (내용)
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        response_data = response.json()
        if "candidates" in response_data:
            return response_data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return f"AI 응답 오류: {response_data}"
    except Exception as e:
        return f"연결 실패: {str(e)}"

def send_telegram_message(message):
    print("LOG: 텔레그램 전송 시도 중...")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": message
        # parse_mode 삭제함 (이게 전송 실패의 주원인입니다)
    }
    response = requests.post(url, json=payload)
    
    # 전송 결과 확인
    if response.status_code == 200:
        print("LOG: ✅ 텔레그램 전송 성공!")
    else:
        print(f"LOG: ❌ 텔레그램 전송 실패! 이유: {response.text}")
        sys.exit(1) # 에러가 나면 Github에서도 빨간불이 뜨게 강제 종료

if __name__ == "__main__":
    briefing = get_news_summary()
    send_telegram_message(briefing)
