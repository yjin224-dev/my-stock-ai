import OpenDartReader
import FinanceDataReader as fdr
from pykrx import stock
import datetime
import pandas as pd
import requests
import os

# 텔레그램 보고용
def send_telegram_msg(text):
    try:
        token = os.environ.get("TELEGRAM_TOKEN")
        chat_id = "8403847596" # 영진님 고유 ID
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={text}"
        requests.get(url, timeout=10)
    except: pass

def standardize_columns(df):
    if df is None or df.empty: return None
    df.columns = [str(c).upper() for c in df.columns]
    mapping = {'종가': 'CLOSE', 'CLOSE': 'CLOSE', '거래량': 'VOLUME', 'VOLUME': 'VOLUME', '거래대금': 'AMOUNT'}
    new_cols = {col: v for col in df.columns for k, v in mapping.items() if k in col}
    df.rename(columns=new_cols, inplace=True)
    return df

def check_elite_and_dart():
    try:
        dart = OpenDartReader(os.environ.get("DART_API_KEY")) # 공시 도구 가동
        now = datetime.datetime.now()
        target_date = now.strftime("%Y%m%d")
        
        # 1. 시장 데이터 가져오기
        df_market = stock.get_market_ohlcv(target_date, market="ALL")
        if df_market is None or df_market.empty:
            df_market = stock.get_market_ohlcv((now - datetime.timedelta(days=1)).strftime("%Y%m%d"), market="ALL")
        
        df_market = standardize_columns(df_market)
        # 거래대금 상위 500개 중 500억 이상 터진 종목 정밀 분석
        df_top = df_market[df_market['AMOUNT'] >= 50_000_000_000].sort_values(by='AMOUNT', ascending=False).head(500)
        
        for ticker in df_top.index:
            try:
                name = stock.get_market_ticker_name(ticker)
                df = fdr.DataReader(ticker, (now - datetime.timedelta(days=100)).strftime('%Y-%m-%d'))
                df = standardize_columns(df)
                
                if df is not None and len(df) > 60:
                    close = df['CLOSE']
                    # 📈 이평선 밀집 (4% 이내) & RSI 분석
                    ma5, ma20, ma60 = close.rolling(5).mean().iloc[-1], close.rolling(20).mean().iloc[-1], close.rolling(60).mean().iloc[-1]
                    ma_diff = (max(ma5, ma20, ma60) - min(ma5, ma20, ma60)) / min(ma5, ma20, ma60)
                    
                    vol_dry = df['VOLUME'].iloc[-3:].mean() < df['VOLUME'].iloc[-20:].mean() * 0.6
                    
                    # 🎯 포착 조건 충족 시
                    if ma_diff < 0.04 and vol_dry:
                        # 🔍 해당 종목의 오늘 주요 공시가 있는지 확인
                        disclosures = dart.list(ticker, start=target_date)
                        disclosure_msg = "\n🔔 최근 공시: 없음"
                        if disclosures is not None and not disclosures.empty:
                            recent_title = disclosures.iloc[0]['report_nm']
                            disclosure_msg = f"\n⚠️ 주요 공시: {recent_title}"

                        amount_bill = round(df_top.loc[ticker, 'AMOUNT'] / 100_000_000)
                        msg = f"💎 [정예+공시 포착] {name}\n💰 거래대금: {amount_bill}억\n📈 밀집도: {ma_diff*100:.1f}%{disclosure_msg}"
                        send_telegram_msg(msg)
            except: continue
        print("분석 완료")
    except Exception as e: print(f"에러: {e}")

if __name__ == "__main__":
    check_elite_and_dart()
