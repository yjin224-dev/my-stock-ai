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

def standardize_columns(df):
    if df is None or df.empty: return None
    df.columns = [str(c).upper() for c in df.columns]
    mapping = {'종가': 'CLOSE', 'CLOSE': 'CLOSE', '거래량': 'VOLUME', 'VOLUME': 'VOLUME', '거래대금': 'AMOUNT'}
    new_cols = {col: v for col in df.columns for k, v in mapping.items() if k in col}
    df.rename(columns=new_cols, inplace=True)
    return df

def check_market_expansion():
    try:
        now = datetime.datetime.now()
        target_date = now.strftime("%Y%m%d")
        df_market = stock.get_market_ohlcv(target_date, market="ALL")
        
        if df_market is None or df_market.empty:
            for i in range(1, 5):
                check_date = (now - datetime.timedelta(days=i)).strftime("%Y%m%d")
                df_market = stock.get_market_ohlcv(check_date, market="ALL")
                if not df_market.empty:
                    target_date = check_date
                    break

        df_market = standardize_columns(df_market)
        # 🔍 1. 감시 범위를 상위 300개로 확대
        df_top = df_market.sort_values(by='AMOUNT', ascending=False).head(300)
        
        found_count = 0
        for ticker in df_top.index:
            try:
                name = stock.get_market_ticker_name(ticker)
                df = fdr.DataReader(ticker, (now - datetime.timedelta(days=100)).strftime('%Y-%m-%d'))
                df = standardize_columns(df)
                
                if df is not None and len(df) > 60:
                    close = df['CLOSE']
                    # 📈 2. 이평선 밀집 조건 유연화 (5% 이내)
                    ma5, ma20, ma60 = close.rolling(5).mean().iloc[-1], close.rolling(20).mean().iloc[-1], close.rolling(60).mean().iloc[-1]
                    ma_diff = (max(ma5, ma20, ma60) - min(ma5, ma20, ma60)) / min(ma5, ma20, ma60)
                    
                    # 📉 3. RSI 보조지표 추가 (과매도 반등 포착용)
                    delta = close.diff()
                    up, down = delta.copy(), delta.copy()
                    up[up < 0], down[down > 0] = 0, 0
                    au = up.rolling(window=14).mean()
                    ad = down.abs().rolling(window=14).mean()
                    rsi = 100 - (100 / (1 + au / ad)).iloc[-1]
                    
                    # 🎯 알림 조건: (이평선 밀집 & 거래량 가뭄) OR (역대급 과매도 RSI < 25)
                    vol_dry = df['VOLUME'].iloc[-3:].mean() < df['VOLUME'].iloc[-20:].mean() * 0.7
                    
                    if (ma_diff < 0.05 and vol_dry) or rsi < 25:
                        reason = "이평선 밀집" if ma_diff < 0.05 else "과매도 반등"
                        msg = f"🔥 [포착] {name}\n🎯 이유: {reason}\n📊 RSI: {rsi:.1f}\n📉 밀집도: {ma_diff*100:.1f}%"
                        send_telegram_msg(msg)
                        found_count += 1
            except: continue
        print(f"분석 완료! {found_count}개 종목 포착")
    except Exception as e: print(f"에러: {e}")

if __name__ == "__main__":
    check_market_expansion()
