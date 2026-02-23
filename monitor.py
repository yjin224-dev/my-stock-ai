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

def check_advanced_signals():
    try:
        now = datetime.datetime.now()
        target_date = now.strftime("%Y%m%d")
        # 최근 3일간의 수급을 확인하기 위한 날짜 설정
        start_date = (now - datetime.timedelta(days=7)).strftime("%Y%m%d")
        
        # 분석 대상: 거래대금 상위 종목군
        df_price = stock.get_market_ohlcv(target_date, market="ALL")
        df_top = df_price.sort_values(by='거래대금', ascending=False).head(100)
        
        for ticker in df_top.index:
            name = stock.get_market_ticker_name(ticker)
            df = fdr.DataReader(ticker, (now - datetime.timedelta(days=60)).strftime('%Y-%m-%d'))
            
            if len(df) > 30:
                # 1. 이평선 밀집도 (에너지 응축)
                ma5 = df['Close'].rolling(5).mean().iloc[-1]
                ma20 = df['Close'].rolling(20).mean().iloc[-1]
                ma60 = df['Close'].rolling(60).mean().iloc[-1]
                ma_diff = (max(ma5, ma20, ma60) - min(ma5, ma20, ma60)) / min(ma5, ma20, ma60)
                
                # 2. 거래량 가뭄 (최근 3일 평균이 20일 평균의 60% 이하)
                vol_dry = df['Volume'].iloc[-3:].mean() < df['Volume'].iloc[-20:].mean() * 0.6
                
                # 3. 기관/외인 쌍끌이 매수 확인
                df_investor = stock.get_market_net_purchases_of_equities_by_ticker(start_date, target_date, ticker)
                is_buying = df_investor.loc[ticker, '기관합계'] > 0 or df_investor.loc[ticker, '외국인합계'] > 0
                
                # 🎯 [필터] 이평선이 3% 이내로 모이고, 거래량이 죽었는데, 수급은 들어올 때
                if ma_diff < 0.03 and vol_dry and is_buying:
                    msg = f"💎 [폭발전야 포착] {name}\n🎯 밀집도: {ma_diff*100:.1f}% (에너지 응축)\n📉 거래량: 가뭄 상태 (매집 완료 의심)\n👤 수급: 기관/외인 매집 중"
                    send_telegram_msg(msg)
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # 공시 체크 함수도 포함되어 있다면 같이 실행
    check_advanced_signals()
