import os
import sys

# 1. 라이브러리 검사
print("--- [진단 시작] 1. 라이브러리 검사 ---")
try:
    import google.generativeai as genai
    import feedparser
    import requests
    import schedule
    print(f"✅ 구글 AI 라이브러리 버전: {genai.__version__}")
except ImportError as e:
    print(f"❌ 라이브러리 설치 실패: {e}")
    sys.exit(1)

# 2. 비밀 열쇠(Secrets) 검사
print("\n--- [진단 시작] 2. 비밀 열쇠 검사 ---")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not GOOGLE_API_KEY:
    print("❌ 에러: 'GOOGLE_API_KEY'가 없습니다! Github Secrets 철자를 확인하세요.")
    sys.exit(1)
else:
    print(f"✅ API 키 확인됨 (앞 5자리: {GOOGLE_API_KEY[:5]}...)")

if not TELEGRAM_TOKEN:
    print("❌ 에러: 'TELEGRAM_TOKEN'이 없습니다!")
    sys.exit(1)
else:
    print("✅ 텔레그램 토큰 확인됨")

if not CHAT_ID:
    print("❌ 에러: 'CHAT_ID'가 없습니다!")
    sys.exit(1)
else:
    print(f"✅ Chat ID 확인됨: {CHAT_ID}")

# 3. AI 모델 연결 테스트
print("\n--- [진단 시작] 3. AI 모델 연결 테스트 ---")
try:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("안녕? 짧게 대답해줘.")
    print(f"✅ AI 응답 성공: {response.text.strip()}")
except Exception as e:
    print(f"❌ AI 연결 실패: {e}")
    # 만약 1.5-flash가 안되면 pro로 재시도
    print("⚠️ 'gemini-pro' 모델로 재시도합니다...")
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("테스트")
        print("✅ gemini-pro 모델은 작동합니다!")
    except Exception as e2:
        print(f"❌ 재시도 실패: {e2}")
        sys.exit(1)

# 4. 뉴스 수집 및 전송 (원래 기능)
print("\n--- [진단 시작] 4. 뉴스 수집 및 전송 ---")
RSS_FEEDS = {
    "국내 정치": "https://www.yna.co.kr/rss/politics.xml",
    "경제": "https://www.mk.co.kr/rss/30000001/"
}

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print(f"❌ 텔레그램 전송 실패: {response.text}")
    else:
        print("✅ 텔레그램 전송 성공!")

def get_news_summary():
    full_content = ""
    for category, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            full_content += f"\n[{category}]\n"
            for entry in feed.entries[:2]:
                full_content += f"- {entry.title}\n"
        except Exception as e:
            print(f"⚠️ {category} 뉴스 수집 중 에러: {e}")

    prompt = f"다음 뉴스를 3줄로 요약해줘:\n{full_content}"
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"분석 실패: {e}"

# 실행
if __name__ == "__main__":
    briefing = get_news_summary()
    print("분석 결과 생성 완료.")
    send_telegram_message(briefing)
    print("🎉 모든 과정이 완료되었습니다!")
