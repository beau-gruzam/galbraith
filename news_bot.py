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

def get_available_models():
    """사용 가능한 모델 목록을 조회합니다 (디버깅용)"""
    url = f"https://generativelanguage.googleapis.com/v1/models?key={GOOGLE_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        if "models" in data:
            # 'generateContent' 기능을 지원하는 모델만 필터링
            names = [m['name'] for m in data['models'] if 'generateContent' in m.get('supportedGenerationMethods', [])]
            return "\n".join(names)
        return f"모델 목록 조회 실패: {data}"
    except Exception as e:
        return f"통신 실패: {str(e)}"

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
    print("LOG: AI 분석 요청 중 (v1 정식 버전)...")
    
    # 🌟 Henry님의 해결책 적용: v1beta -> v1 으로 변경
    # 모델명도 최신 정식 명칭인 'gemini-1.5-flash' 사용
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GOOGLE_API_KEY}"
    
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

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        data = response.json()
        
        if "candidates" in data:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            # 🌟 만약 또 실패하면? -> 사용 가능한 모델 목록을 조회해서 알려줌
            print(f"LOG: 1.5-flash 실패. 원인: {data}")
            available_models = get_available_models()
            error_message = (
                f"🚨 모델 접속 오류 (v1 시도)\n\n"
                f"구글이 현재 Henry님의 키로 허용하는 모델 목록은 아래와 같습니다:\n"
                f"------------------\n"
                f"{available_models}\n"
                f"------------------\n"
                f"위 목록에 있는 이름으로 코드를 수정하면 100% 해결됩니다."
            )
            return error_message

    except Exception as e:
        return f"통신 에러: {str(e)}"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, json=payload)

if __name__ == "__main__":
    briefing = get_news_summary()
    send_telegram_message(briefing)
