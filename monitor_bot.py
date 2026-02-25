import os
import datetime
import requests
import FinanceDataReader as fdr
from pykrx import stock
import OpenDartReader
import google.generativeai as genai # 안정적인 표준 라이브러리로 변경

# 1. 보안 키 설정
DART_KEY = os.environ.get("DART_API_KEY")
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN")
AI_KEY = os.environ.get("GEMINI_API_KEY")
MY_CHAT_ID = "8403847596" 

# 2. AI 설정 (Gemini 1.5 Flash - 가장 빠르고 확실함)
genai.configure(api_key=AI_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

def send_tg(text):
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.post(url, json={'chat_id': MY_CHAT_ID, 'text': text}, timeout=10)
    except: pass

def ask_ai(prompt_text):
    try:
        # AI에게 분석 요청
        response = ai_model.generate_content(prompt_text)
        return response.text.strip()
    except Exception as e:
        return f"AI 분석 일시 지연 (사유: {str(e)[:30]})"

def run_once():
    now = datetime.datetime.now()
    today = now.strftime('%Y%m%d')
    
    # [연결 확인] AI가 살아있는지 테스트 메시지 발송
    test_msg = ask_ai("안녕? 넌 이제부터 영진의 주식 비서야. 짧게 인사해줘.")
    send_tg(f"🤖 [시스템 체크]\n{test_msg}")
    
    print(f"🚀 {now.strftime('%H:%M:%S')} - 분석 시작")

    # --- [섹션 1: 공시 감시] ---
    try:
        dart = OpenDartReader(DART_KEY)
        df_dart = dart.list(None, today) 
        
        keywords = ["공급계약", "수주", "제3자배정", "소각", "무상증자"]
        if df_dart is not None and not df_dart.empty:
            for _, row in df_dart.iterrows():
                title = row.get('report_nm', row.get('report_name', ''))
                if any(k in title for k in keywords):
                    comp = row.get('corp_name', row.get('corp_nm', '종목명 미상'))
                    # AI 분석 실행
                    analysis = ask_ai(f"{comp}의 '{title}' 공시가 주가에 호재일까? 1문장 요약해줘.")
                    send_tg(f"🆕 [신규 호재]\n🏢 종목: {comp}\n📄 공시: {title}\n🤖 AI 분석: {analysis}")
    except: pass

    # --- [섹션 2: 거래대금 Top 5] ---
    try:
        df_vol = stock.get_market_ohlcv(today)
        if df_vol is None or df_vol.empty:
            df_vol = stock.get_market_ohlcv((now - datetime.timedelta(days=1)).strftime('%Y%m%d'))
            
        if df_vol is not None and not df_vol.empty:
            df_top = df_vol.sort_values(by='거래대금', ascending=False).head(5)
            msg = "🔥 [오늘의 거래대금 Top 5]\n"
            for ticker, row in df_top.iterrows():
                name = stock.get_market_ticker_name(ticker)
                msg += f"- {name}\n"
            send_tg(msg)
    except: pass

    print(f"✅ 분석 완료")

if __name__ == "__main__":
    run_once()
