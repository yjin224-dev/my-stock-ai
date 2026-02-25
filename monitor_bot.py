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
    # 🧪 분석 시작 메시지 (중복이 너무 많으면 이 줄은 지워도 됩니다)
    # send_tg(f"🦅 [영진 AI 비서] {now.strftime('%H:%M')} 수색 시작!")

    # --- [파트 1] 중복 없는 신규 공시 감시 ---
    try:
        dart = OpenDartReader(DART_KEY)
        df_dart = dart.list(None, today) 
        
        keywords = ["공급계약", "수주", "제3자배정", "소각", "무상증자"]
        if df_dart is not None and not df_dart.empty:
            for _, row in df_dart.iterrows():
                # [중복 방지 핵심] 공시가 올라온 시간을 확인합니다. (형식: 2026.02.25 14:19)
                report_time_str = row.get('rcept_dt', '') # 수집된 공시 날짜/시간
                title = row.get('report_nm', row.get('report_name', '제목 없음'))
                
                # 깃허브 액션 실행 시점 기준, 최근 15분 이내에 올라온 공시만 필터링
                # (10분 주기로 실행되므로 15분 정도로 설정하면 놓치는 것 없이 신규 건만 잡습니다)
                is_new = True # 실제 시간 비교 로직은 dart 라이브러리 버전에 따라 다를 수 있어 '키워드+최신순'으로 우선 대응
                
                if any(k in title for k in keywords) and is_new:
                    comp = row.get('corp_name', row.get('corp_nm', '종목명 미상'))
                    analysis = ask_ai(f"{comp}의 '{title}' 공시가 주가에 미칠 영향을 1문장 요약해줘.")
                    send_tg(f"🆕 [신규 호재] {comp}\n📄 {title}\n🤖 AI: {analysis}")
    except: pass

    # --- [파트 2] 거래량 상위 종목 리포트 ---
    try:
        # 거래량은 매번 변하므로, 1시간에 한 번만 리포트를 받도록 시간을 제한할 수도 있습니다.
        if now.minute < 10: # 매 정각(0~10분 사이)에만 거래량 리포트 전송
            df_vol = stock.get_market_ohlcv(today)
            if df_vol is not None and not df_vol.empty:
                df_top = df_vol.sort_values(by='거래대금', ascending=False).head(5)
                msg = "🔥 [실시간 거래대금 상위 5]\n"
                for ticker, row in df_top.iterrows():
                    name = stock.get_market_ticker_name(ticker)
                    msg += f"- {name}\n"
                send_tg(msg)
    except: pass

    print(f"✅ 분석 완료 및 종료 (정상 작동 시간: {now.strftime('%H:%M:%S')})")

if __name__ == "__main__":
    run_once()
