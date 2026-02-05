import feedparser
import requests
import os
import datetime
import json
import time
from youtube_transcript_api import YouTubeTranscriptApi

# 1. 환경변수 설정
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# 🌟 Henry님이 설정하신 채널
YOUTUBE_CHANNELS = {
    "📺 겸손은힘들다": "UCAAvO0ehWox1bbym3rXKBZw" 
}

def get_video_transcript(video_id):
    """자막 추출 함수"""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko', 'en'])
        full_text = " ".join([t['text'] for t in transcript_list])
        return full_text[:15000] 
    except:
        return None

def get_yesterday_videos():
    """어제~오늘 올라온 영상만 수집"""
    summary_data = ""
    print("LOG: 유튜브 채널 스캔 중...")
    
    # 기준 시간: 현재로부터 24시간 전
    one_day_ago = time.time() - (24 * 60 * 60)
    
    # 🌟 수정 1: 영상 개수를 세기 위한 변수 초기화
    video_count = 0

    for name, channel_id in YOUTUBE_CHANNELS.items():
        try:
            rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            feed = feedparser.parse(rss_url)
            
            found_video = False
            for entry in feed.entries:
                published_time = time.mktime(entry.published_parsed)
                
                if published_time > one_day_ago:
                    # 🌟 수정 2: 영상을 찾으면 카운트 증가
                    video_count += 1
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
            
    # 🌟 수정 3: 텍스트와 개수, 2가지를 반환하도록 수정 (에러 해결 핵심!)
    return summary_data, video_count

def analyze_youtube(content):
    """AI 분석 함수 (재시도 로직 포함)"""
    if not content.strip():
        return "오늘은(지난 24시간) 모니터링 대상 채널에 올라온 새 영상이 없습니다."

    print("LOG: 유튜브 내용 AI 분석 중 (Gemini 2.5 Flash)...")
    
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GOOGLE_API_KEY}"
    
    prompt = f"""
    당신은 핵심 정보를 요약해주는 '유튜브 큐레이터'입니다.
    어제 올라온 주요 정치/사회/경제/투자 유튜브 영상들의 자막 내용을 분석하여 핵심을 브리핑하세요.

    [작성 원칙]
    1. **영상별 요약:** 각 영상의 핵심 주장을 3개의 글머리 기호로 요약할 것.
    2. **시사점:** 이 영상 내용이 정책 기획자와 주식 투자자에게 어떤 의미가 있는지 각각 한 문장으로 코멘트할 것.
    3. **가독성:** 채널명과 제목을 명확히 구분하고 이모지 활용.

    [영상 데이터]
    {content}

    [출력 양식]
    📺 {datetime.date.today()} 유튜브 일일 요약

    1. (채널명) - (영상 제목)
    ▪️ (요약 1)
    ▪️ (요약 2)
    ▪️ (요약 3)
    💡 시사점: (한 줄 정리)

    (반복...)
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                data = response.json()
                if "candidates" in data:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
            
            print(f"LOG: 시도 {attempt+1}/{max_retries} 실패. 상태코드: {response.status_code}")
            
            if response.status_code >= 500:
                print("LOG: 서버 오류(500) 감지. 5초 후 재시도합니다...")
                time.sleep(5)
                continue
            else:
                return f"🚨 분석 실패 (클라이언트 오류): {response.text}"

        except Exception as e:
            print(f"LOG: 통신 에러 발생: {e}")
            time.sleep(5)

    return "🚨 서버가 혼잡하여 3번 재시도했으나 실패했습니다. 잠시 후 다시 실행해주세요."

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, json=payload)

if __name__ == "__main__":
    # 이제 여기서 에러가 나지 않습니다 (2개를 받고 2개를 받으니까요)
    youtube_content, count = get_yesterday_videos()
    
    if count > 0:
        # 함수 이름도 analyze_youtube로 통일했습니다
        briefing = analyze_youtube(youtube_content)
        send_telegram_message(briefing)
    else:
        print("LOG: 분석할 영상이 없습니다.")
        send_telegram_message(f"📺 {datetime.date.today()} 유튜브 요약: 지난 24시간 동안 올라온 새 영상이 없습니다.")
