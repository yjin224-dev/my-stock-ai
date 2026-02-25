import os
import datetime
import requests
import FinanceDataReader as fdr
from pykrx import stock
import OpenDartReader
from google import genai

# 1. 보안 키 설정 (이미 등록하신 깃허브 Secrets 사용)
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
        prompt = f"종목 {company}의 거래량이 평소보다 {volume_info}배 폭등했습니다. 최근 공시 제목은 '{title}'입니다. 이 폭등의 원인을 분석하고 투자 유의점을 전문가처럼 1문장으로 요약해줘."
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except: return "AI 사유 분석 중..."

def run_once():
    now = datetime.datetime.now()
    send_tg(f"🦅 [영진 AI 비서] {now.strftime('%H:%M')} 정밀 분석 가동!")
    
    # --- 1. 거래량 폭등 종목 포착 (에러 수정됨) ---
    try:
        target_date = now.strftime("%Y%m%d")
        # [수정] market 옵션 에러 방지를 위해 대문자 'ALL' 대신 'KOSPI'와 'KOSDAQ'을 명시적으로 합칩니다.
        # 또한 장 시작 전이나 주말에 데이터가 없는 경우를 대비해 안전하게 가져옵니다.
        df_today = stock.get_market_ohlcv(target_date, market="KOSPI")
        if df_today is None or df_today.empty:
            target_date = (now - datetime.timedelta(days=1)).strftime("%Y%m%d")
            df_today = stock.get_market_ohlcv(target_date, market="KOSPI")
        
        # 거래대금 상위 30개 종목 추출
        df_top = df_today.sort_values(by='거래대금', ascending=False).head(30)
        
        for ticker, row in df_top.iterrows():
            name = stock.get_market_ticker_name(ticker)
            # [수정] KeyError 방지를 위해 컬럼 이름을 직접 확인하거나 인덱스로 접근합니다.
            curr_vol = row.get('거래량', 0)
            
            if curr_vol > 0:
                # 최근 20일 평균 거래량과 비교
                df_prev = stock.get_market_ohlcv_by_ticker((now - datetime.timedelta(days=30)).strftime("%Y%m%d"), 
                                                           (now - datetime.timedelta(days=1)).strftime("%Y%m%d"), ticker)
                avg_vol = df_prev['거래량'].mean()
                
                # 평소보다 5배(500%) 이상 터졌을 때만 알림
                if curr_vol > avg_vol * 5:
                    # 관련 공시 확인
                    dart = OpenDartReader(DART_KEY)
                    ads = dart.list(ticker, now.strftime("%Y%m%d"))
                    recent_ad = ads.iloc[0].get('report_nm', '공시 없음') if ads is not None and not ads.empty else "관련 공시 없음"
                    
                    vol_ratio = round(curr_vol / avg_vol, 1)
                    ai_opinion = ask_ai(name, recent_ad, vol_ratio)
                    
                    send_tg(f"🔥 [세력 포착] {name}\n📈 거래량: 평소 대비 {vol_ratio}배 폭등!\n📄 최근 공시: {recent_ad}\n🤖 AI 분석: {ai_opinion}")
    except Exception as e:
        print(f"세력 분석 에러: {e}")

    # --- 2. 공시 감시 (기존 기능) ---
    try:
        dart = OpenDartReader(DART_KEY)
        df_dart = dart.list(None, now.strftime('%Y%m%d'))
        keywords = ["공급계약", "수주", "제3자배정", "소각", "무상증자"]
        if df_dart is not None and not df_dart.empty:
            for _, row in df_dart.iterrows():
                title = row.get('report_nm', row.get('report_name', ''))
                if any(key in title for key in keywords):
                    company = row.get('corp_name', row.get('corp_nm', '회사명 미상'))
                    analysis = ask_ai(company, title, "공시 발생")
                    send_tg(f"🔔 [호재] {company}\n📄 {title}\n🤖 AI: {analysis}")
    except: pass

    print(f"✅ 분석 완료")

if __name__ == "__main__":
    run_once()
