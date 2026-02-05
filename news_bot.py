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
    print("LOG: AI 분석 요청 중...")
    
    # 모델: 호환성이 확인된 gemini-pro 사용
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GOOGLE_API_KEY}"
    
    prompt = f"""
    당신은 17년차 정책 지원관이자 거시경제 전문가입니다.
    아래 뉴스 헤드라인을 보고 '정책적 함의'와 '경제적 영향'을 중심으로 브리핑해 주세요.
    특수문자 없이 텍스트로만 요약해주세요.

    [뉴스 데이터]
    {full_content}

    [출력 양식]
    📅 {datetime.date.today()} Henry의 모닝 브리핑

    1. 정치/정책
    (내용)

    2. 경제/금융
    (내용)

    3. 국제 정세
    (내용)

    💡 한 줄 인사이트: (내용)
    """

    # 🌟 핵심 수정: 안전 필터(Safety Settings) 완전 해제
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        data = response.json()
        
        # 정상 응답 확인
        if "candidates" in data:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            # 🌟 에러 발생 시: 폰으로 에러 내용을 직접 전송 (디버깅용)
            error_msg = json.dumps(data, indent=2, ensure_ascii=False)
            print(f"LOG: AI 응답 실패: {error_msg}")
            return f"🚨 AI 오류 발생 (이 내용을 보여주세요):\n{error_msg[:1000]}"

    except Exception as e:
        return f"통신 에러: {str(e)}"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, json=payload)

if __name__ == "__main__":
    briefing = get_news_summary()
    send_telegram_message(briefing)
