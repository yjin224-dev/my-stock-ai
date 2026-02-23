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

# 💡 이름표가 무엇이든 'Close', 'Volume' 등으로 통일하는 무적 함수
def standardize_df(df):
    if df is None or df.empty: return None
    mapping = {
        '종가': 'Close', 'close': 'Close', '거래량': 'Volume', 'volume': 'Volume',
        '시가': 'Open', 'open': 'Open', '고가': 'High', 'high': 'High',
        '저가': 'Low', 'low': 'Low', '거래대금': 'Amount'
    }
    # 실제 존재하는 컬럼들만 골라서 이름을 바꿉니다.
    new_cols = {col: mapping[col] for col in df.columns if col in mapping}
    df.rename(columns=new_cols, inplace=True)
    return df

def check_market():
    try:
        now = datetime.datetime.now()
        # 🔍 [핵심] 오늘 데이터가 없으면 가장 최근 영업일 데이터를 자동으로 찾습니다.
        target_date = stock.get_nearest_business_day_in_range(now.strftime("%Y%m%d"))
        print(f"[{now}] 분석 기준일: {target_date}")

        # 1. 시장 전체 데이터 가져오기
        df_market = stock.get_market_ohlcv(target_date, market="ALL")
        df_market = standardize_df(df_market)
        
        if df_market is None or 'Amount' not in df_market.columns:
            print("데이터를 불러오지 못했습니다. 잠시 후 다시 시도합니다.")
            return

        # 거래대금 상위 100개 추출
        df_top = df_market.sort_values(by='Amount', ascending=False).head(100)
        
        found_count = 0
        for ticker in df_top.index:
            try:
                name = stock.get_market_ticker_name(ticker)
                # 개별 종목 60일치 데이터
                df = fdr.DataReader(ticker, (now - datetime.timedelta(days=60)).strftime('%Y-%m-%d'))
                df = standardize_df(df)
                
                if df is not None and len(df) > 30 and 'Close' in df.columns:
                    # 📈 이평선 밀집도 (3% 이내)
                    ma5 = df['Close'].rolling(5).mean().iloc[-1]
                    ma20 = df['Close'].rolling(20).mean().iloc[-1]
                    ma60 = df['Close'].rolling(60).mean().iloc[-1]
                    ma_diff = (max(ma5, ma20, ma60) - min(ma5, ma20, ma60)) / min(ma5, ma20, ma60)
                    
                    # 📉 거래량 가뭄 (최근 3일 평균이 20일 평균의 60% 이하)
                    vol_avg = df['Volume'].iloc[-20:].mean()
                    vol_recent = df['Volume'].iloc[-3:].mean()
                    
                    if ma_diff < 0.03 and vol_recent < vol_avg * 0.6:
                        msg = f"💎 [폭발전야 포착] {name}\n🎯 밀집도: {ma_diff*100:.1f}%\n📉 거래량: 가뭄 (매집 의심)"
                        send_telegram_msg(msg)
                        found_count += 1
            except: continue 
            
        print(f"분석 완료! 포착 종목: {found_count}개")
        
    except Exception as e:
        print(f"❌ 최종 에러 확인: {e}")

if __name__ == "__main__":
    check_market()
