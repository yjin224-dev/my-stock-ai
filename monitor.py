import OpenDartReader
import FinanceDataReader as fdr
from pykrx import stock
import datetime
import pandas as pd
import requests
import os

def send_telegram_msg(text):
    try:
        token = os.environ.get("TELEGRAM_TOKEN")
        chat_id = "8403847596" # 영진님 고유 ID
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={text}"
        requests.get(url, timeout=10)
    except: pass

def check_elite_stocks():
    try:
        now = datetime.datetime.now()
        target_date = now.strftime("%Y%m%d")
        
        # 1. 시장 데이터 가져오기 (오늘 데이터가 없으면 전날 데이터로 자동 전환)
        df_market = stock.get_market_ohlcv(target_date, market="ALL")
        if df_market is None or df_market.empty:
            target_date = (now - datetime.timedelta(days=1)).strftime("%Y%m%d")
            df_market = stock.get_market_ohlcv(target_date, market="ALL")

        # 💡 [무적 로직 1] 이름표 대신 '6번째 칸'을 거래대금으로 인식합니다.
        # pykrx의 표준 데이터 순서: 시가, 고가, 저가, 종가, 거래량, 거래대금(Index 5)
        df_top = df_market.sort_values(by=df_market.columns[5], ascending=False).head(300)
        
        found_count = 0
        for ticker in df_top.index:
            try:
                name = stock.get_market_ticker_name(ticker)
                # 2. 개별 종목 60일치 데이터 확보
                df = fdr.DataReader(ticker, (now - datetime.timedelta(days=100)).strftime('%Y-%m-%d'))
                
                if df is not None and len(df) > 30:
                    # 💡 [무적 로직 2] 이름표 무시! 데이터 '위치'로 강제 추출
                    # 보통 OHLCV 순서: [0:시가, 1:고가, 2:저가, 3:종가, 4:거래량]
                    close_data = df.iloc[:, 3] # 4번째 컬럼 (종가)
                    vol_data = df.iloc[:, 4]   # 5번째 컬럼 (거래량)
                    
                    # 📈 이동평균선(MA) 계산
                    ma5 = close_data.rolling(5).mean().iloc[-1]
                    ma20 = close_data.rolling(20).mean().iloc[-1]
                    ma60 = close_data.rolling(60).mean().iloc[-1]
                    
                    # 이평선 밀집도 계산: $$ma\_diff = \frac{\max(ma5, ma20, ma60) - \min(ma5, ma20, ma60)}{\min(ma5, ma20, ma60)}$$
                    ma_diff = (max(ma5, ma20, ma60) - min(ma5, ma20, ma60)) / min(ma5, ma20, ma60)
                    
                    # 📉 거래량 가뭄 확인 (최근 3일 평균이 20일 평균의 70% 이하)
                    vol_avg = vol_data.rolling(20).mean().iloc[-1]
                    vol_recent = vol_data.iloc[-3:].mean()
                    
                    if ma_diff < 0.04 and vol_recent < vol_avg * 0.7:
                        amount_bill = round(df_top.loc[ticker, df_market.columns[5]] / 100_000_000)
                        msg = f"💎 [포착] {name}\n💰 거래대금: {amount_bill}억\n📈 밀집도: {ma_diff*100:.1f}%\n📉 거래량: 가뭄상태"
                        send_telegram_msg(msg)
                        found_count += 1
            except: continue # 특정 종목 분석 실패 시 중단 없이 다음 종목 진행

        print(f"[{now}] 분석 완료! 포착 종목: {found_count}개")
        
    except Exception as e:
        print(f"❌ 최종 에러 확인: {e}")

if __name__ == "__main__":
    check_elite_stocks()
