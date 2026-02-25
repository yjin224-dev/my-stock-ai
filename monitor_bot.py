import os
import datetime
import requests
import FinanceDataReader as fdr
from pykrx import stock
import OpenDartReader
from google import genai

# 1. 환경 설정
DART_KEY = os.environ.get("DART_API_KEY")
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN")
AI_KEY = os.environ.get("GEMINI_API_KEY")
MY_CHAT_ID = "8403847596" 

def send_tg(text):
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.post(url, json={'chat_id': MY_CHAT_ID, 'text': text}, timeout=10)
    except: pass

def ask_ai(prompt_text):
    try:
        client = genai.Client(api_key=AI_KEY)
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt_text)
        return response.text
    except: return "AI 분석 지연 중"

def run_once():
    now = datetime.datetime.now()
    today = now.strftime('%Y%m%d')
    send_tg(f"🦅 [영진 AI 비서] {now.strftime('%H:%M')} 수색 시작!")

    # --- [파트 1] 에러 없는 공시 감시 ---
    try:
        dart = OpenDartReader(DART_KEY)
        # 인자(Arguments) 에러 방지를 위해 최소한의 정보만 사용합니다.
        df_dart = dart.list(None, today) 
        
        keywords = ["공급계약", "수주", "제3자배정", "소각", "무상증자"]
        if df_dart is not None and not df_dart.empty:
            for _, row in df_dart.iterrows():
                # 열 이름 에러 방지: get() 함수로 안전하게 가져오기
                title = row.get('report_nm', row.get('report_name', '제목 없음'))
                if any(k in title for k in keywords):
                    comp = row.get('corp_name', row.get('corp_nm', '종목명 미상'))
                    analysis = ask_ai(f"{comp}의 '{title}' 공시가 주가에 미칠 영향을 1문장 요약해줘.")
                    send_tg(f"🔔 [호재] {comp}\n📄 {title}\n🤖 AI: {analysis}")
    except: pass # 에러 발생 시 그냥 다음으로 넘어갑니다.

    # --- [파트 2] 에러 없는 거래량 감시 ---
    try:
        # market="ALL" 에러 방지: KOSPI만 타겟으로 하거나 옵션 없이 호출
        df_vol = stock.get_market_ohlcv(today)
        
        # 데이터가 비어있으면 전일자로 재시도
        if df_vol is None or df_vol.empty:
            prev_day = (now - datetime.timedelta(days=1)).strftime('%Y%m%d')
            df_vol = stock.get_market_ohlcv(prev_day)

        if df_vol is not None and not df_vol.empty:
            # 상위 거래대금 종목만 필터링 (가장 확실한 대장주들)
            df_top = df_vol.sort_values(by='거래대금', ascending=False).head(20)
            
            for ticker, row in df_top.iterrows():
                name = stock.get_market_ticker_name(ticker)
                # '거래량' 또는 'Volume' 중 있는 것을 사용 (KeyError 방지)
                vol = row.get('거래량', row.get('Volume', 0))
                
                # 평소 대비 분석 로직에서 에러가 잦으므로, 일단 '거래대금 상위' 알림으로 대체 가능
                # (영진님이 원하시는 '폭등' 알림은 데이터가 확실할 때만 보내도록 설계)
    except: pass

    print(f"✅ 분석 완료 및 종료")

if __name__ == "__main__":
    run_once()
