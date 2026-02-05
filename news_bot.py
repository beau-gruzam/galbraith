import feedparser
import requests
import os
import datetime
import json

# --- 설정값 ---
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# --- 뉴스 소스 ---
RSS_FEEDS = {
    "🏛 국내 정치/정책": "https://www.yna.co.kr/rss/politics.xml",
    "💰 경제/금융": "https://www.mk.co.kr/rss/30000001/",
    "🌍 국제 정세 (BBC)": "http://feeds.bbci.co.uk/news/world/rss.xml",
}

def get_news_summary():
    # 1. 뉴스 수집
    full_content = ""
    print("뉴스 수집 중...")
    for category, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            full_content += f"\n[{category}]\n"
            for entry in feed.entries[:3]:
                full_content += f"- {entry.title}\n"
        except Exception as e:
            print(f"{category} 에러: {e}")

    # 2. AI 분석 (라이브러리 없이 직접 요청 - 무적 방식)
    print("AI 분석 요청 중...")
    
    # Gemini 1.5 Flash 공식 API 주소
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GOOGLE_API_KEY}"
    
    # Henry님 맞춤 프롬프트
    prompt = f"""
    당신은 17년차 정책 지원관이자 거시경제 전문가입니다.
    아래 뉴스 헤드라인을 보고 '정책적 함의'와 '경제적 영향'을 중심으로 브리핑해 주세요.
    
    [뉴스 내용]
    {full_content}
    
    [출력 양식]
    📅 {datetime.date.today()} Henry의 모닝 브리핑
    
    1. 🏛 정치/정책 핵심
    (내용 분석)
    
    2. 💰 경제/금융 흐름
    (시장 영향)
    
    3. 🌍 국제 이슈
    (요약)
    
    💡 한 줄 인사이트: (결론)
    """
    
    # 데이터 포장
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        response_data = response.json()
        
        # 응답에서 텍스트만 쏙 뽑아내기
        if "candidates" in response_data:
            return response_data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return f"AI 응답 오류: {response_data}"
            
    except Exception as e:
        return f"연결 실패: {str(e)}"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": message, 
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    briefing = get_news_summary()
    send_telegram_message(briefing)
    print("완료")
