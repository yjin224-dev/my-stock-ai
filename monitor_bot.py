import os
import datetime
import requests
import FinanceDataReader as fdr
from pykrx import stock
import OpenDartReader
from google import genai

# 1. 보안 키 설정
DART_KEY = os.environ.get("DART_API_KEY")
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN")
AI_KEY = os.environ.get("GEMINI_API_KEY")
MY_CHAT_ID = "8403847596" 

def send_tg(text):
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.post(url, json={'chat_id': MY_CHAT_ID, 'text': text}, timeout=10)
    except: pass

def ask_ai(content):
    try:
        client = genai.Client(api_key=AI_KEY)
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=f"주식 전문가로서 이 공시 제목이 호재인지 판단해서 1문장 요약해줘: {content}"
        )
        return response.text
    except: return "AI 분석 지연"

def run_once():
    now = datetime.datetime.now()
    # 시작 인사 (이게 오면 연결은 100% 성공입니다!)
    send_tg(f"🦅 [영진 AI 비서] {now.strftime('%H:%M')} 분석을 가동합니다.")
    
    print(f"🚀 {now.strftime('%H:%M:%S')} - 분석 시작")

    # --- 공시 감시 (에러 해결 핵심 구간) ---
    try:
        dart = OpenDartReader(DART_KEY)
        today = now.strftime('%Y%m%d')
        
        # [수정] 키워드 인자 대신 위치 인자를 사용하여 모든 버전에서 작동하게 만듭니다.
        # list(종목명, 시작날짜) 순서입니다.
        df = dart.list(None, today) 
        
        keywords = ["공급계약", "수주", "제3자배정", "소각", "무상증자", "특허"]
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                title = row['report_nm']
                if any(key in title for key in keywords):
                    ai_opinion = ask_ai(title)
                    send_tg(f"🔔 [호재] {row['corp_nm']}\n📄 {title}\n🤖 AI: {ai_opinion}")
    except Exception as e:
        # 에러가 나도 멈추지 않고 로그를 남기게 함
        print(f"❌ 공시 분석 에러: {e}") 

    print(f"✅ 분석 완료")

if __name__ == "__main__":
    run_once()
