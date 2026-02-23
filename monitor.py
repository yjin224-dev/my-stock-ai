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

# 💡 [무적 로직] 어떤 이름표가 오든 표준 영어 이름으로 강제 변환합니다.
def standardize_columns(df):
    if df is None or df.empty: return None
    # 모든 컬럼명을 대문자로 변환하여 비교를 단순화합니다.
    df.columns = [str(c).upper() for c in df.columns]
    mapping = {
        '종가': 'CLOSE', 'CLOSE': 'CLOSE', '거래량': 'VOLUME', 'VOLUME': 'VOLUME',
        '시가': 'OPEN', 'OPEN': 'OPEN', '고가': 'HIGH', 'HIGH': 'HIGH',
        '저가': 'LOW', 'LOW': 'LOW', '거래대금': 'AMOUNT', 'AMOUNT': 'AMOUNT', 'VALUE': 'AMOUNT'
    }
    new_cols = {}
    for col in df.columns:
        for k, v in mapping.items():
            if k in col: # '종가(원)' 처럼 이름이 길어도 '종가'가 포함되면 매칭
                new_cols[col] = v
                break
    df.rename(columns=new_cols, inplace=True)
    return df

def check_market():
    try:
        now = datetime.datetime.now()
        target_date = now.strftime("%Y%m%d")
        
        # 1. 최근 영업일 데이터 확보
        df_market = stock.get_market_ohlcv(target_date, market="ALL")
        if df_market is None or df_market.empty:
            for i in range(1, 10):
                check_date = (now - datetime.timedelta(days=i)).strftime("%Y%m%d")
                df_market = stock.get_market_ohlcv(check_date, market="ALL")
                if df_market is not None and not df_market.empty:
                    target_date = check_date
                    break

        print(f"[{now}] 분석 기준일: {target_date}")
        df_market = standardize_columns(df_market)
        
        if df_market is None or 'AMOUNT' not in df_market.columns:
            print("시장 데이터를 가져오지 못했습니다.")
            return

        # 거래대금 상위 100개 추출
        df_top = df_market.sort_values(by='AMOUNT', ascending=False).head(100)
        
        found_count = 0
        for ticker in df_top.index:
            try:
                name = stock.get_market_ticker_name(ticker)
                df = fdr.DataReader(ticker, (now - datetime.timedelta(days=60)).strftime('%Y-%m-%d'))
                df = standardize_columns(df)
                
                if df is not None and len(df) > 30 and 'CLOSE' in df.columns:
                    # 📈 이평선 밀집도 계산 (5, 20, 60일선이 3% 이내)
                    ma5 = df['CLOSE'].rolling(5).mean().iloc[-1]
                    ma20 = df['CLOSE'].rolling(20).mean().iloc[-1]
                    ma60 = df['CLOSE'].rolling(60).mean().iloc[-1]
                    
                    ma_max, ma_min = max(ma5, ma20, ma60), min(ma5, ma20, ma60)
                    ma_diff = (ma_max - ma_min) / ma_min
                    
                    # 📉 거래량 가뭄 확인
                    vol_avg = df['VOLUME'].iloc[-20:].mean()
                    vol_recent = df['VOLUME'].iloc[-3:].mean()
                    
                    if ma_diff < 0.03 and vol_recent < vol_avg * 0.6:
                        msg = f"💎 [폭발전야 포착] {name}\n🎯 밀집도: {ma_diff*100:.1f}%\n📉 거래량: 가뭄 (매집 의심)"
                        send_telegram_msg(msg)
                        found_count += 1
            except: continue 
            
        print(f"분석 완료! 포착 종목: {found_count}개")
        
    except Exception as e:
        print(f"❌ 최종 에러 상세 정보: {e}")

if __name__ == "__main__":
    check_market()
