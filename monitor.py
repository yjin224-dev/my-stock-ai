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

# 💡 [핵심] 어떤 이름표가 오든 표준 영어 이름으로 강제 변환
def standardize_df(df):
    if df is None or df.empty: return None
    # 모든 컬럼명을 대문자 문자열로 변환하여 비교를 단순화합니다.
    df.columns = [str(c).upper() for c in df.columns]
    mapping = {
        '종가': 'CLOSE', 'CLOSE': 'CLOSE', '거래량': 'VOLUME', 'VOLUME': 'VOLUME',
        '시가': 'OPEN', 'OPEN': 'OPEN', '고가': 'HIGH', 'HIGH': 'HIGH',
        '저가': 'LOW', 'LOW': 'LOW', '거래대금': 'AMOUNT', 'AMOUNT': 'AMOUNT'
    }
    new_cols = {}
    for col in df.columns:
        for k, v in mapping.items():
            if k in col: # '종가(원)' 처럼 이름이 길어도 '종가'가 포함되면 매칭
                new_cols[col] = v
                break
    df.rename(columns=new_cols, inplace=True)
    return df

def check_elite_and_dart():
    try:
        now = datetime.datetime.now()
        target_date = now.strftime("%Y%m%d")
        print(f"[{now}] 분석 시작 (기준일: {target_date})")
        
        # 1. 시장 데이터 가져오기
        df_market = stock.get_market_ohlcv(target_date, market="ALL")
        if df_market is None or df_market.empty:
            df_market = stock.get_market_ohlcv((now - datetime.timedelta(days=1)).strftime("%Y%m%d"), market="ALL")
        
        df_market = standardize_df(df_market)
        
        # 거래대금이 있는 컬럼을 찾아 500억 이상 종목 추출
        amt_col = 'AMOUNT' if 'AMOUNT' in df_market.columns else df_market.columns[5]
        df_top = df_market[df_market[amt_col] >= 50_000_000_000].sort_values(by=amt_col, ascending=False).head(300)
        
        found_count = 0
        for ticker in df_top.index:
            try:
                name = stock.get_market_ticker_name(ticker)
                df = fdr.DataReader(ticker, (now - datetime.timedelta(days=100)).strftime('%Y-%m-%d'))
                df = standardize_df(df)
                
                if df is not None and len(df) > 30 and 'CLOSE' in df.columns:
                    close = df['CLOSE']
                    # 📈 이평선 밀집도 계산
                    ma5, ma20, ma60 = close.rolling(5).mean().iloc[-1], close.rolling(20).mean().iloc[-1], close.rolling(60).mean().iloc[-1]
                    
                    # 수식: $$ma\_diff = \frac{max(ma) - min(ma)}{min(ma)}$$
                    ma_diff = (max(ma5, ma20, ma60) - min(ma5, ma20, ma60)) / min(ma5, ma20, ma60)
                    
                    vol_recent = df['VOLUME'].iloc[-3:].mean()
                    vol_avg = df['VOLUME'].iloc[-20:].mean()
                    
                    if ma_diff < 0.04 and vol_recent < vol_avg * 0.7:
                        amount_bill = round(df_top.loc[ticker, amt_col] / 100_000_000)
                        msg = f"💎 [포착] {name}\n💰 거래대금: {amount_bill}억\n📈 밀집도: {ma_diff*100:.1f}%"
                        send_telegram_msg(msg)
                        found_count += 1
            except: continue
            
        print(f"✅ 분석 완료! 포착된 종목 수: {found_count}")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    check_elite_and_dart()
