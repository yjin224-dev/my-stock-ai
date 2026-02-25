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

def ask_ai(company, title, volume_info):
    try:
        client = genai.Client(api_key=AI_KEY)
        # AI에게 거래량 폭등 이유와 공시의 연관성을 묻습니다.
        prompt = f"종목 {company}의 거래량이 평소보다 {volume_info} 터졌습니다. 최근 공시 제목은 '{title}'입니다. 이 폭등의 원인을 분석하고 투자 유의점을 1문장으로 요약해줘."
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except: return "사유 분석 중..."

def run_once():
    now = datetime.datetime.now()
    send_tg(f"🦅 [영진 AI 비서] {now.strftime('%H:%M')} 정밀 수색을 시작합니다.")
    
    # --- 1. 거래량 폭등 종목 포착 (500% 기준) ---
    try:
        target_date = now.strftime("%Y%m%d")
        # 오늘 거래량 가져오기
        df_today = stock.get_market_ohlcv(target_date, market="ALL")
        if df_today is None or df_today.empty:
            target_date = (now - datetime.timedelta(days=1)).strftime("%Y%m%d")
            df_today = stock.get_market_ohlcv(target_date, market="ALL")

        # 전일 거래량과 비교 (정밀 분석을 위해 상위 거래대금 50개 선정)
        df_today = df_today.sort_values(by='거래대금', ascending=False).head(50)
        
        for ticker, row in df_today.iterrows():
            name = stock.get_market_ticker_name(ticker)
            curr_vol = row['거래량']
            
            # 과거 20일 평균 거래량 계산
            df_prev = stock.get_market_ohlcv_by_ticker((now - datetime.timedelta(days=30)).strftime("%Y%m%d"), 
                                                       (now - datetime.timedelta(days=1)).strftime("%Y%m%d"), ticker)
            avg_vol = df_prev['거래량'].mean()
            
            # 500% (5배) 폭등 여부 확인
            if curr_vol > avg_vol * 5:
                # 관련 공시가 있는지 확인
                dart = OpenDartReader(DART_KEY)
                ads = dart.list(ticker, now.strftime("%Y%m%d"))
                recent_ad = ads.iloc[0]['report_nm'] if ads is not None and not ads.empty else "관련 공시 없음"
                
                ai_analysis = ask_ai(name, recent_ad, f"{round(curr_vol/avg_vol, 1)}배")
                
                msg = f"🔥 [세력 포착] {name}\n📈 거래량: 평소 대비 {round(curr_vol/avg_vol, 1)}배 폭등!\n📄 최근 공시: {recent_ad}\n🤖 AI 사유 요약: {ai_analysis}"
                send_tg(msg)
                
    except Exception as e:
        print(f"세력 분석 에러: {e}")

    print(f"✅ 분석 완료")

if __name__ == "__main__":
    run_once()
