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
    # 시작 인사
    send_tg(f"🦅 [영진 AI 비서] {now.strftime('%H:%M')} 분석을 시작합니다.")
    
    print(f"🚀 {now.strftime('%H:%M:%S')} - 분석 시작")

    # --- 공시 감시 (이름표 에러 완벽 해결) ---
    try:
        dart = OpenDartReader(DART_KEY)
        today = now.strftime('%Y%m%d')
        
        # 최신 공시 리스트 가져오기
        df = dart.list(None, today) 
        
        keywords = ["공급계약", "수주", "제3자배정", "소각", "무상증자", "특허"]
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                # 'report_nm'이 없으면 'report_name'을 찾아보는 식으로 안전하게 가져옵니다.
                title = row.get('report_nm', row.get('report_name', '제목 없음'))
                
                if any(key in title for key in keywords):
                    ai_opinion = ask_ai(title)
                    # 회사 이름도 'corp_name' 또는 'corp_nm' 중 있는 것을 사용합니다.
                    company = row.get('corp_name', row.get('corp_nm', '회사명 미상'))
                    
                    send_tg(f"🔔 [호재] {company}\n📄 {title}\n🤖 AI: {ai_opinion}")
    except Exception as e:
        print(f"❌ 공시 분석 에러: {e}") 

    print(f"✅ 분석 완료")

if __name__ == "__main__":
    run_once()
