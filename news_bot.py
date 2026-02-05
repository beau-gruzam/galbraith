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

# 🌟 소스 구성: 미국증시 + 국내경제 + 국내정치(New)
RSS_FEEDS = {
    "🇺🇸 미국 증시/글로벌": "https://www.hankyung.com/feed/globalmarket",   # 한경 글로벌마켓
    "💰 국내 경제/금융": "https://www.mk.co.kr/rss/30000001/",           # 매일경제
    "🏛 정치/사회 파장": "https://www.yna.co.kr/rss/politics.xml",        # 연합뉴스 정치
}

def get_news_summary():
    full_content = ""
    print("LOG: 하이브리드 데이터 수집 중...")
    for category, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            full_content += f"\n[{category}]\n"
            # 정치/사회는 중요한 것만 골라야 하므로 넉넉히 수집해서 AI가 고르게 함
            limit = 4 if "정치" in category else 3
            for index, entry in enumerate(feed.entries[:limit], 1):
                full_content += f"{index}. {entry.title}\n"
        except Exception as e:
            print(f"LOG: {category} 수집 실패: {e}")

    print("LOG: 투자 영향력 분석 중 (Gemini 2.5 Flash)...")
    
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GOOGLE_API_KEY}"
    
    # 🌟 프롬프트: 정치 이슈를 경제적 관점에서 해석하도록 지시
    prompt = f"""
    당신은 연금펀드와 ISA 계좌를 운용하는 '매크로 투자 전략가'입니다.
    수집된 뉴스를 바탕으로 한국 및 미국 주식시장에 미칠 영향을 분석해 주세요.

    [투자자 프로필]
    - 자산 구성: 지수추종 ETF(S&P500, 나스닥100, KOSPI200) 및 배당 ETF
    - 관심사: 정책 변화가 내 계좌에 미칠 영향 (규제, 세금, 부양책 등)

    [작성 원칙 - 수량 엄수]
    1. **미국 증시:** 간밤의 마감 시황과 핵심 변수(금리, 빅테크) 분석.
    2. **정치/사회:** 시장에 영향을 줄 수 있는 **중대 이슈 딱 2가지만** 엄선할 것. (단순 정쟁 제외, 정책/규제 위주)
    3. **대응 전략:** 이 뉴스들이 ETF 투자자에게 주는 함의를 명확히 할 것.
    4. **형식:** 이모지(🇺🇸, 🏛, 🇰🇷) 사용, 가독성 좋은 개조식.

    [뉴스 데이터]
    {full_content}

    [출력 양식]
    📅 {datetime.date.today()} Henry의 투자 인사이트

    1. 🇺🇸 간밤의 월스트리트 (미국 마감)
    🔹 3대 지수 & 시장 분위기
     ▪️ (요약 및 상승/하락 원인)
    🔹 주목할 빅테크 & 이슈
     ▪️ (특이사항)

    2. 🏛 국내 정치/사회 리스크 (핵심 2선)
    🔹 (이슈 1 제목)
     ▪️ 시장 영향: (이 정책/이슈가 주식시장이나 특정 섹터에 미칠 파장)
    
    🔹 (이슈 2 제목)
     ▪️ 시장 영향: (규제 완화, 세법 개정, 사회적 갈등 등 경제적 관점 분석)

    3. 🇰🇷 한국 시장 & ETF 대응 전략
    🔹 오늘 국장 예상 흐름
     ▪️ (전망)
    🔹 연금/ISA 투자자 행동 가이드
     ▪️ (예: "정치 테마주 주의, 지수형 ETF는 저가 매수 기회" 등 구체적 조언)

    💡 오늘의 한 줄 요약: (투자 심리를 관통하는 문장)
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
