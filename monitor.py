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

# 💡 이름표가 한글이든 영어든 무조건 'Close', 'Volume'으로 바꿔주는 마법의 함수
def force_standard_columns(df):
    if df is None or df.empty: return df
    # 모든 가능성 있는 이름들을 표준 영어 이름으로 매핑합니다.
    mapping = {
        '종가': 'Close', 'close': 'Close', 'Close': 'Close',
        '거래량': 'Volume', 'volume': 'Volume', 'Volume': 'Volume',
        '시가': 'Open', 'open': 'Open', 'Open': 'Open',
        '고가': 'High', 'high': 'High', 'High': 'High',
        '저가': 'Low', 'low': 'Low', 'Low': 'Low'
    }
    # 데이터프레임의 컬럼명을 순회하며 매핑된 이름이 있으면 변경합니다.
    new_cols = {col: mapping[col] for col in df.columns if col in mapping}
    df.rename(columns=new_cols, inplace=True)
    return df

def check_market():
    try:
        now = datetime.datetime.now()
        target_date = now.strftime("%Y%m%d")
        print(f"[{now}] 분석을 시작합니다...")

        # 1. 시장 전체 데이터 가져오기 (보통 한글 '종가' 등으로 옴)
        df_market = stock.get_market_ohlcv(target_date, market="ALL")
        df_market = force_standard_columns(df_market)
        
        # 거래대금 상위 100개 추출
        df_top = df_market.sort_values(by='거래대금', ascending=False).head(100)
        
        found_count = 0
        for ticker in df_top.index:
            name = stock.get_market_ticker_name(ticker)
            # 2. 개별 종목 상세 데이터 (보통 영어 'Close' 등으로 옴)
            df = fdr.DataReader(ticker, (now - datetime.timedelta(days=60)).strftime('%Y-%m-%d'))
            df = force_standard_columns(df)
            
            if df is not None and len(df) > 30 and 'Close' in df.columns:
                # 📈 이평선 밀집도 계산 (3% 이내)
                ma5 = df['Close'].rolling(5).mean().iloc[-1]
                ma20 = df['Close'].rolling(20).mean().iloc[-1]
                ma60 = df['Close'].rolling(60).mean().iloc[-1]
                
                ma_diff = (max(ma5, ma20, ma60) - min(ma5, ma20, ma60)) / min(ma5, ma20, ma60)
                
                # 📉 거래량 가뭄 확인 (최근 3일 평균이 20일 평균의 60% 이하)
                vol_avg = df['Volume'].iloc[-20:].mean()
                vol_recent = df['Volume'].iloc[-3:].mean()
                
                if ma_diff < 0.03 and vol_recent < vol_avg * 0.6:
                    msg = f"💎 [폭발전야 포착] {name}\n🎯 밀집도: {ma_diff*100:.1f}%\n📉 거래량: 가뭄상태 (매집 의심)"
                    send_telegram_msg(msg)
                    found_count += 1
        
        print(f"분석 완료! 포착된 종목 수: {found_count}")
        
    except Exception as e:
        print(f"❌ 오류 발생 상세: {e}")

if __name__ == "__main__":
    check_market()
