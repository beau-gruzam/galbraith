import feedparser
import requests
import os
import datetime
import json
import time
import re
from youtube_transcript_api import YouTubeTranscriptApi

# 1. 환경변수 설정
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# 🌟 모니터링할 채널
YOUTUBE_CHANNELS = {
    "📺 겸손은힘들다": "UCAAvO0ehWox1bbym3rXKBZw"
}

def clean_text(text):
    """HTML 태그 제거 및 텍스트 정리"""
    clean = re.sub('<.*?>', '', text) # HTML 태그 제거
    return clean.strip()

def get_video_content(entry):
    """자막 추출 시도 -> 실패 시 영상 설명(Description) 가져오기"""
    video_id = entry.yt_videoid
    title = entry.title
    
    # 1. 자막(Script) 추출 시도
    try:
        # 한국어(ko), 한국어-대한민국(ko-KR), 영어(en) 순서로 시도
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko', 'ko-KR', 'en'])
        
        full_text = " ".join([t['text'] for t in transcript_list])
        print(f"LOG: [{title}] ✅ 자막 추출 성공! (길이: {len(full_text)})")
        
        # AI 입력 한계 및 비용 고려하여 10,000자 제한
        return f"[자막 데이터]\n{full_text[:10000]}", "자막 기반"
        
    except Exception as e:
        print(f"LOG: [{title}] ❌ 자막 없음/실패 ({e}) -> 영상 설명(Description)으로 대체합니다.")
        
        # 2. 자막 실패 시: 영상 설명(Description) 가져오기
        # feedparser에서 'summary'나 'media_description'에 설명이 들어있음
        description = ""
        if 'summary' in entry:
            description = clean_text(entry.summary)
        elif 'media_description' in entry:
            description = clean_text(entry.media_description)
            
        if description:
            print(f"LOG: 설명 데이터 확보 (길이: {len(description)})")
            return f"[영상 설명 데이터]\n{description}", "설명 기반"
        else:
            return None, "데이터 없음"

def get_yesterday_videos():
    """어제~오늘 올라온 영상만 수집"""
    summary_data = ""
    print("LOG: 유튜브 채널 스캔 중...")
    
    # 기준 시간: 24시간 전
    one_day_ago = time.time() - (24 * 60 * 60)
    video_count = 0

    for name, channel_id in YOUTUBE_CHANNELS.items():
        try:
            rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            feed = feedparser.parse(rss_url)
            
            for entry in feed.entries:
                published_time = time.mktime(entry.published_parsed)
                
                if published_time > one_day_ago:
                    video_count += 1
                    print(f"LOG: 발견! [{name}] {entry.title}")
                    
                    # 자막 또는 설명 가져오기
                    content_text, source_type = get_video_content(entry)
                    
                    if content_text:
                        summary_data += f"\n[채널: {name} | 분석출처: {source_type}]\n제목: {entry.title}\n{content_text}\n{'-'*30}\n"
                    else:
                        summary_data += f"\n[채널: {name}]\n제목: {entry.title}\n(분석 불가: 자막 및 설명 없음)\n{'-'*30}\n"
                        
        except Exception as e:
            print(f"LOG: {name} RSS 파싱 에러 - {e}")
            
    return summary_data, video_count

def analyze_youtube(content):
    """AI 분석 함수"""
    if not content.strip():
        return "최근 24시간 내 올라온 영상이 없습니다."

    print("LOG: AI 심층 분석 요청 중 (Gemini 2.5 Flash)...")
    
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GOOGLE_API_KEY}"
    
    prompt = f"""
    당신은 17년차 정책/시사 전문 분석가입니다.
    제공된 유튜브 영상 데이터(자막 또는 설명)를 바탕으로 '내용 요약'을 수행하세요.

    [작성 원칙]
    1. **내용 파악:** '자막 데이터'가 있으면 대화 내용을 요약하고, '영상 설명 데이터'만 있으면 출연진과 주제 위주로 요약하세요.
    2. **개별 분석:** 각 영상마다 구체적으로 어떤 이야기가 오갔는지(Who said What)를 파악하려고 노력하세요.
    3. **단순 나열 금지:** "방송을 했다"가 아니라 "무슨 주장을 했다"를 적으세요.

    [데이터]
    {content}

    [출력 양식]
    📺 {datetime.date.today()} 유튜브 심층 브리핑

    1. (채널명) - (영상 제목)
    🏷 (분석 출처 표기: 자막 or 설명)
    ▪️ 핵심 주제: (한 줄 요약)
    ▪️ 주요 내용:
      - (출연진 발언이나 핵심 논거 요약 1)
      - (출연진 발언이나 핵심 논거 요약 2)
    💡 시사점: (정책/사회적 함의)

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
            
            print(f"LOG: 시도 {attempt+1}/{max_retries} 실패. 코드: {response.status_code}")
            
            if response.status_code >= 500:
                time.sleep(5)
                continue
            else:
                return f"🚨 분석 실패: {response.text}"

        except Exception as e:
            print(f"LOG: 통신 에러: {e}")
            time.sleep(5)

    return "🚨 서버 혼잡으로 분석에 실패했습니다."

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, json=payload)

if __name__ == "__main__":
    youtube_content, count = get_yesterday_videos()
    
    if count > 0:
        briefing = analyze_youtube(youtube_content)
        send_telegram_message(briefing)
    else:
        print("LOG: 분석할 영상이 없습니다.")
        send_telegram_message(f"📺 {datetime.date.today()} 유튜브: 지난 24시간 동안 새 영상이 없습니다.")
