import os
import datetime
import requests
import FinanceDataReader as fdr
from pykrx import stock
import OpenDartReader
from google import genai

# 1. 보안 키 설정 (깃허브 Secrets 사용)
DART_KEY = os.environ.get("DART_API_KEY")
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN")
AI_KEY = os.environ.get("GEMINI_API_KEY")
MY_CHAT_ID = "8403847596" # 영진님의 텔레그램 ID

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
            contents=f"주식 전문가로서 이 공시 제목이 호재인지 요약해줘: {content}"
        )
        return response.text
    except: return "AI 분석 지연"

def run_once():
    now = datetime.datetime.now()
    # 🧪 테스트용: 실행 즉시 텔레그램 발송 (이게 오면 연결 성공입니다!)
    send_tg(f"🦅 [영진 AI 비서] {now.strftime('%H:%M')} 분석을 시작합니다.")
    
    print(f"🚀 {now.strftime('%H:%M:%S')} - 분석 시작")

    # --- 공시 감시 (에러 수정됨) ---
    try:
        dart = OpenDartReader(DART_KEY)
        today = now.strftime('%Y%m%d')
        # 에러 해결: 파라미터를 bgn_date로 수정하거나 생략하여 최신순으로 가져옵니다.
        df = dart.list(bgn_date=today) 
        
        keywords = ["공급계약", "수주", "제3자배정", "소각", "무상증자"]
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                title = row['report_nm']
                if any(key in title for key in keywords):
                    ai_opinion = ask_ai(title)
                    send_tg(f"🔔 [호재] {row['corp_nm']}\n📄 {title}\n🤖 AI: {ai_opinion}")
    except Exception as e:
        print(f"❌ 공시 분석 에러: {e}")
        send_tg(f"⚠️ 공시 분석 중 오류가 발생했습니다: {e}")

    print(f"✅ 분석 완료")

if __name__ == "__main__":
    run_once()
