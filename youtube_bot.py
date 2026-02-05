import feedparser
import requests
import os
import datetime
import json
import time
from youtube_transcript_api import YouTubeTranscriptApi

# 1. 환경변수 설정 (기존 키 그대로 사용)
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# 🌟 모니터링할 유튜브 채널 목록 (원하는 채널 ID로 변경하세요)
YOUTUBE_CHANNELS = {
    "📺 삼프로TV": "UChXVXPZGk355O3e2jXf0qaw",
    "📺 겸손은힘들다": "UCAAvO0ehWox1bbym3rXKBZw",
    "📺 월가아재": "UCS2X_k78qQyH9WzJ-6y1Gsg" 
}

def get_video_transcript(video_id):
    """자막 추출 함수"""
    try:
        # 한국어 우선, 없으면 영어 등 다른 언어 시도
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko', 'en'])
        full_text = " ".join([t['text'] for t in transcript_list])
        return full_text[:15000] # AI 입력 한계 고려 (충분히 김)
    except:
        return None

def get_yesterday_videos():
    """어제~오늘 올라온 영상만 수집"""
    summary_data = ""
    print("LOG: 유튜브 채널 스캔 중...")
    
    # 기준 시간: 현재로부터 24시간 전
    one_day_ago = time.time() - (24 * 60 * 60)

    for name, channel_id in YOUTUBE_CHANNELS.items():
        try:
            rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            feed = feedparser.parse(rss_url)
            
            found_video = False
            for entry in feed.entries:
                # 영상 업로드 시간 확인 (published_parsed)
                published_time = time.mktime(entry.published_parsed)
                
                # 24시간 이내에 올라온 영상인가?
                if published_time > one_day_ago:
                    found_video = True
                    print(f"LOG: 발견! [{name}] {entry.title}")
                    
                    transcript = get_video_transcript(entry.yt_videoid)
                    if transcript:
                        summary_data += f"\n[채널: {name}]\n제목: {entry.title}\n내용: {transcript}\n{'-'*30}\n"
                    else:
                        summary_data += f"\n[채널: {name}]\n제목: {entry.title}\n(자막 없음 - 제목만 전달)\n{'-'*30}\n"
            
            if not found_video:
                print(f"LOG: {name} - 최근 24시간 내 업로드 없음")

        except Exception as e:
            print(f"LOG: {name} 에러 - {e}")
            
    return summary_data

def analyze_youtube(content):
    if not content.strip():
        return "오늘은(지난 24시간) 모니터링 대상 채널에 올라온 새 영상이 없습니다. 푹 쉬세요! 🍵"

    print("LOG: 유튜브 내용 AI 분석 중 (Gemini 2.5 Flash)...")
    
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GOOGLE_API_KEY}"
    
    prompt = f"""
    당신은 핵심 정보를 요약해주는 '유튜브 큐레이터'입니다.
    어제 올라온 주요 정치/사회/경제/투자 유튜브 영상들의 자막 내용을 분석하여 핵심을 브리핑하세요.

    [작성 원칙]
    1. **영상별 요약:** 각 영상의 핵심 주장을 4~5개의 글머리 기호로 요약할 것.
    2. **시사점:** 이 영상 내용이 정책 기획자와 주식 투자자에게 어떤 의미가 있는지 각각 한 문장으로 코멘트할 것.
    3. **가독성:** 채널명과 제목을 명확히 구분하고 이모지 활용.

    [영상 데이터]
    {content}

    [출력 양식]
    📺 {datetime.date.today()} 유튜브 일일 요약

    1. (채널명) - (영상 제목)
    ▪️ (핵심 내용 1)
    ▪️ (핵심 내용 2)
    ▪️ (핵심 내용 3)
    💡 투자 포인트: (내용)

    (다음 영상 이어짐...)
    """

    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        data = response.json()
        if "candidates" in data:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return f"🚨 분석 실패: {data}"
    except Exception as e:
        return f"통신 에러: {str(e)}"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, json=payload)

if __name__ == "__main__":
    youtube_content = get_yesterday_videos()
    briefing = analyze_youtube(youtube_content)
    send_telegram_message(briefing)
