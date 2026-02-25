import os
import datetime
import requests
import FinanceDataReader as fdr
from pykrx import stock
import OpenDartReader
from google import genai

# 1. 깃허브 Secrets에서 키 가져오기
DART_KEY = os.environ.get("DART_API_KEY")
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN")
AI_KEY = os.environ.get("GEMINI_API_KEY")
MY_CHAT_ID = "8403847596" # 영진님 텔레그램 ID

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
            contents=f"주식 전문가로서 이 공시 제목이 호재인지 악재인지 판단해서 1문장으로 핵심만 요약해줘: {content}"
        )
        return response.text
    except: return "AI 분석 일시적 지연"

def run_once():
    now = datetime.datetime.now()
    print(f"🚀 {now.strftime('%H:%M:%S')} - 분석 시작")
    
    # --- 공시 감시 로직 ---
    try:
        dart = OpenDartReader(DART_KEY)
        today = now.strftime('%Y%m%d')
        df = dart.list(end_date=today)
        positive_keywords = ["공급계약", "수주", "제3자배정", "자기주식취득", "소각", "무상증자", "특허"]
        
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                title = row['report_nm']
                company = row['corp_nm']
                for key in positive_keywords:
                    if key in title:
                        ai_opinion = ask_ai(title)
                        msg = f"🔔 [호재 공시] {company}\n📄 {title}\n🤖 AI 분석: {ai_opinion}"
                        send_tg(msg)
    except: pass

    # --- 세력 포착 로직 ---
    try:
        target_date = today
        df_price = stock.get_market_ohlcv(target_date, market="ALL")
        if df_price is None or df_price.empty:
            target_date = (now - datetime.timedelta(days=1)).strftime("%Y%m%d")
            df_price = stock.get_market_ohlcv(target_date, market="ALL")
        
        df_top = df_price.sort_values(by=df_price.columns[5], ascending=False).head(30)
        for ticker in df_top.index:
            name = stock.get_market_ticker_name(ticker)
            # 여기에 상세 세력 분석 로직 추가 가능
    except: pass

    print(f"✅ 분석 완료 및 종료")

if __name__ == "__main__":
    run_once()
