import feedparser
import google.generativeai as genai
import requests
import os
import datetime

# --- 설정값 (Github Secrets에서 가져옵니다) ---
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# --- 뉴스 소스 설정 (Henry님의 관심사 반영) ---
# 정책, 경제, 국제 정세 위주
RSS_FEEDS = {
    "국내 정치/정책": "https://www.yna.co.kr/rss/politics.xml",  # 연합뉴스 정치
    "국내 경제/금융": "https://www.mk.co.kr/rss/30000001/",     # 매일경제
    "국제 정세 (BBC)": "http://feeds.bbci.co.uk/news/world/rss.xml", # BBC World
}

def get_news_summary():
    # 1. 뉴스 데이터 수집
    full_content = ""
    for category, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        full_content += f"\n[{category} 주요 헤드라인]\n"
        # 각 카테고리별 최신 기사 5개만 추출
        for entry in feed.entries[:5]:
            full_content += f"- {entry.title}\n"

    # 2. Gemini AI에게 분석 요청 (Henry님 맞춤 프롬프트)
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    당신은 17년 경력의 베테랑 정책 전문가이자 거시경제 분석가입니다.
    아래 뉴스 헤드라인들을 바탕으로, 오늘 아침 내가 꼭 알아야 할 내용을 브리핑해주세요.

    [분석 원칙]
    1. 단순 나열 금지. 핵심 흐름을 꿰뚫어볼 것.
    2. '정책적 시사점'과 '경제/시장(주식, ETF)에 미칠 영향'을 중심으로 해설할 것.
    3. 말투는 정중하면서도 명쾌한 보고서 스타일로 (예: "~할 것으로 보입니다.", "~에 주목해야 합니다.")

    [뉴스 데이터]
    {full_content}

    [출력 양식]
    📅 {datetime.date.today()} 아침 브리핑

    1. 🏛 정치/정책 이슈
    (내용 및 정책적 함의 분석)

    2. 💰 경제/금융 흐름
    (시장 영향 및 투자 관점 해설)

    3. 🌍 글로벌/국제 정세
    (주요 이슈 및 파급 효과)

    💡 오늘의 한 줄 인사이트: (전체 흐름을 요약하는 핵심 문장)
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 분석 중 오류가 발생했습니다: {str(e)}"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown" # 가독성을 위해 마크다운 적용
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    print("뉴스 분석을 시작합니다...")
    briefing = get_news_summary()
    send_telegram_message(briefing)
    print("전송 완료!")
