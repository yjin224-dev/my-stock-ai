import OpenDartReader
import FinanceDataReader as fdr
from pykrx import stock
import datetime
import pandas as pd
import requests
import os

def send_telegram_msg(text):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = "8403847596" # 영진님 고유 ID
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={text}"
    requests.get(url)

# 💡 어떤 이름표가 오든 표준 영어 이름표로 바꿔주는 함수
def standardize_df(df):
    if df is None or df.empty: return None
    mapping = {
        '종가': 'Close', 'close': 'Close', '거래량': 'Volume', 'volume': 'Volume',
        '시가': 'Open', 'open': 'Open', '고가': 'High', 'high': 'High',
        '저가': 'Low', 'low': 'Low', '거래대금': 'Amount'
    }
    new_cols = {col: mapping[col] for col in df.columns if col in mapping}
    df.rename(columns=new_cols, inplace=True)
    return df

def check_market():
    try:
        now = datetime.datetime.now()
        # 🔍 [수정] 명령어 대신 직접 최근 영업일을 찾습니다.
        target_date = now.strftime("%Y%m%d")
        df_market = stock.get_market_ohlcv(target_date, market="ALL")
        
        # 오늘 데이터가 없으면(주말/휴일/장전), 최근 4일치를 뒤져서 장이 열렸던 날을 찾습니다.
        if df_market is None or df_market.empty:
            for i in range(1, 5):
                check_date = (now - datetime.timedelta(days=i)).strftime("%Y%m%d")
                df_market = stock.get_market_ohlcv(check_date, market="ALL")
                if not df_market.empty:
                    target_date = check_date
                    break
        
        print(f"[{now}] 분석 기준일: {target_date}")
        df_market = standardize_df(df_market)
        
        if df_market is None or 'Amount' not in df_market.columns:
            print("데이터를 불러오지 못했습니다.")
            return

        # 거래대금 상위 100개 분석
        df_top = df_market.sort_values(by='Amount', ascending=False).head(100)
        
        found_count = 0
        for ticker in df_top.index:
            try:
                name = stock.get_market_ticker_name(ticker)
                # 개별 종목 60일치 상세 데이터
                df = fdr.DataReader(ticker, (now - datetime.timedelta(days=60)).strftime('%Y-%m-%d'))
                df = standardize_df(df)
                
                if df is not None and len(df) > 30 and 'Close' in df.columns:
                    # 📈 이평선 밀집도 계산 (3% 이내)
                    ma5 = df['Close'].rolling(5).mean().iloc[-1]
                    ma20 = df['Close'].rolling(20).mean().iloc[-1]
                    ma60 = df['Close'].rolling(60).mean().iloc[-1]
                    ma_diff = (max(ma5, ma20, ma60) - min(ma5, ma20, ma60)) / min(ma5, ma20, ma60)
                    
                    # 📉 거래량 가뭄 확인
                    vol_avg = df['Volume'].iloc[-20:].mean()
                    vol_recent = df['Volume'].iloc[-3:].mean()
                    
                    # 🎯 폭발전야 조건 충족 시 알림
                    if ma_diff < 0.03 and vol_recent < vol_avg * 0.6:
                        msg = f"💎 [폭발전야 포착] {name}\n🎯 밀집도: {ma_diff*100:.1f}%\n📉 거래량: 가뭄상태 (매집 의심)"
                        send_telegram_msg(msg)
                        found_count += 1
            except: continue 
            
        print(f"분석 완료! 포착 종목: {found_count}개")
        
    except Exception as e:
        print(f"❌ 최종 에러 확인: {e}")

if __name__ == "__main__":
    check_market()
