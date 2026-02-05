import feedparser
from google import genai
import requests
import os
import datetime

# --- 설정값 가져오기 ---
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# --- 뉴스 소스 (Henry님의 관심사) ---
RSS_FEEDS = {
    "🏛 국내 정치/정책": "https://www.yna.co.kr/rss/politics.xml",
    "💰 경제/금융": "https://www.mk.co.kr/rss/30000001/",
    "🌍 국제 정세 (BBC)": "http://feeds.bbci.co.uk/news/world/rss.xml",
}

def get_news_summary():
    # 1. 뉴스 수집
    full_content = ""
    print("뉴스 수집 시작...")
    for category, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            full_content += f"\n[{category} 헤드라인]\n"
            for entry in feed.entries[:3]: # 카테고리별 3개씩
                full_content += f"- {entry.title}\n"
        except Exception as e:
            print(f"{category} 수집 중 에러: {e}")

    # 2. AI 분석 (신형 Google GenAI SDK 사용)
    print("AI 분석 시작...")
    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)
        
        prompt = f"""
        당신은 17년 경력의 베테랑 정책 전문가이자 거시경제 분석가입니다.
        아래 뉴스 헤드라인들을 바탕으로, 오늘 아침 내가 꼭 알아야 할 내용을 브리핑해주세요.

        [분석 원칙]
        1. 단순 나열 금지. 핵심 흐름을 꿰뚫어볼 것.
        2. '정책적 시사점'과 '경제/시장(주식, ETF)에 미칠 영향'을 중심으로 해설할 것.
        3. 말투는 정중하면서도 명쾌한 보고서 스타일로.

        [뉴스 데이터]
        {full_content}

        [출력 양식]
        📅 {datetime.date.today()} Henry의 모닝 브리핑

        1. 🏛 정치/정책 이슈
        (내용 및 정책적 함의)

        2. 💰 경제/금융 흐름
        (시장 영향 및 투자 관점)

        3. 🌍 국제 정세
        (주요 이슈 요약)

        💡 오늘의 한 줄 인사이트: (전체 요약)
        """

        # 최신 모델 gemini-1.5-flash 사용
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return response.text
        
    except Exception as e:
        return f"AI 분석 중 오류가 발생했습니다: {str(e)}"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown" # 가독성 좋게
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    briefing = get_news_summary()
    send_telegram_message(briefing)
    print("브리핑 전송 완료!")
