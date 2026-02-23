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

# 💡 이름표를 영어로 통일해주는 마법의 함수
def unify_columns(df):
    cols = {
        '시가': 'Open', '고가': 'High', '저가': 'Low', '종가': 'Close', '거래량': 'Volume',
        'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'
    }
    df.rename(columns=cols, inplace=True)
    return df

def check_advanced_signals():
    try:
        now = datetime.datetime.now()
        target_date = now.strftime("%Y%m%d")
        start_date = (now - datetime.timedelta(days=7)).strftime("%Y%m%d")
        
        # 1. 시장 전체 데이터 가져오기 (pykrx는 보통 한글 사용)
        df_price = stock.get_market_ohlcv(target_date, market="ALL")
        df_price = unify_columns(df_price) # 한글 -> 영어로 강제 변환
        
        # 거래대금 상위 100개 분석
        df_top = df_price.sort_values(by='거래대금', ascending=False).head(100)
        
        for ticker in df_top.index:
            name = stock.get_market_ticker_name(ticker)
            df = fdr.DataReader(ticker, (now - datetime.timedelta(days=60)).strftime('%Y-%m-%d'))
            
            if df is not None and len(df) > 30:
                df = unify_columns(df) # 어떤 데이터든 영어로 통일
                
                # 2. 이평선 밀집도 계산 (이제 무조건 'Close'만 쓰면 됩니다!)
                ma5 = df['Close'].rolling(5).mean().iloc[-1]
                ma20 = df['Close'].rolling(20).mean().iloc[-1]
                ma60 = df['Close'].rolling(60).mean().iloc[-1]
                ma_diff = (max(ma5, ma20, ma60) - min(ma5, ma20, ma60)) / min(ma5, ma20, ma60)
                
                # 3. 거래량 가뭄 확인
                vol_dry = df['Volume'].iloc[-3:].mean() < df['Volume'].iloc[-20:].mean() * 0.6
                
                # 4. 수급 확인
                df_investor = stock.get_market_net_purchases_of_equities_by_ticker(start_date, target_date, ticker)
                is_buying = df_investor.loc[ticker, '기관합계'] > 0 or df_investor.loc[ticker, '외국인합계'] > 0
                
                # 🎯 폭발전야 조건 충족 시 알림
                if ma_diff < 0.03 and vol_dry and is_buying:
                    msg = f"💎 [폭발전야 포착] {name}\n🎯 밀집도: {ma_diff*100:.1f}%\n📉 거래량: 가뭄 (매집 의심)\n👤 수급: 기관/외인 매집"
                    send_telegram_msg(msg)
                    
    except Exception as e:
        print(f"오류 내용: {e}")

if __name__ == "__main__":
    check_advanced_signals()
