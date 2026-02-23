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

# 💡 이름표를 무조건 영어 표준으로 통일해주는 함수
def fix_columns(df):
    if df is None or df.empty: return df
    # 한글과 영어 이름을 모두 대응시켜서 표준화합니다.
    mapping = {
        '시가': 'Open', '고가': 'High', '저가': 'Low', '종가': 'Close', '거래량': 'Volume',
        'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'
    }
    df.rename(columns=mapping, inplace=True)
    return df

def check_signals():
    try:
        now = datetime.datetime.now()
        target_date = now.strftime("%Y%m%d")
        
        # 1. 시장 전체 데이터 가져오기 (pykrx 사용)
        df_market = stock.get_market_ohlcv(target_date, market="ALL")
        df_market = fix_columns(df_market) # 즉시 영어로 통일
        
        # 거래대금 상위 100개 분석
        df_top = df_market.sort_values(by='거래대금', ascending=False).head(100)
        
        for ticker in df_top.index:
            name = stock.get_market_ticker_name(ticker)
            # fdr로 상세 데이터 가져오기
            df = fdr.DataReader(ticker, (now - datetime.timedelta(days=60)).strftime('%Y-%m-%d'))
            df = fix_columns(df) # 즉시 영어로 통일
            
            if df is not None and len(df) > 30:
                # 2. 이평선 밀집도 계산 (이제 안전하게 'Close'만 사용)
                ma5 = df['Close'].rolling(5).mean().iloc[-1]
                ma20 = df['Close'].rolling(20).mean().iloc[-1]
                ma60 = df['Close'].rolling(60).mean().iloc[-1]
                
                ma_max = max(ma5, ma20, ma60)
                ma_min = min(ma5, ma20, ma60)
                ma_diff = (ma_max - ma_min) / ma_min
                
                # 3. 거래량 가뭄 확인
                vol_avg = df['Volume'].iloc[-20:].mean()
                vol_recent = df['Volume'].iloc[-3:].mean()
                
                # 🎯 폭발전야 조건: 이평선 밀집(3%이내) + 거래량 급감(평균의 60%이하)
                if ma_diff < 0.03 and vol_recent < vol_avg * 0.6:
                    msg = f"💎 [폭발전야 포착] {name}\n🎯 밀집도: {ma_diff*100:.1f}%\n📉 거래량: 가뭄상태 (매집의심)"
                    send_telegram_msg(msg)
                    
    except Exception as e:
        print(f"오류 상세: {e}")

if __name__ == "__main__":
    check_signals()
