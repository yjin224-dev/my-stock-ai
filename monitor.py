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
        start_date = (now - datetime.timedelta(days=7)).strftime("%Y%m%d")
        
        df_price = stock.get_market_ohlcv(target_date, market="ALL")
        df_top = df_price.sort_values(by='거래대금', ascending=False).head(100)
        
        for ticker in df_top.index:
            name = stock.get_market_ticker_name(ticker)
            df = fdr.DataReader(ticker, (now - datetime.timedelta(days=60)).strftime('%Y-%m-%d'))
            
            if df is not None and len(df) > 30:
                # 🔍 [핵심 수정] 한글/영어 컬럼명 자동 대응
                col_close = 'Close' if 'Close' in df.columns else '종가'
                col_vol = 'Volume' if 'Volume' in df.columns else '거래량'
                
                # 1. 이평선 밀집도
                ma5 = df[col_close].rolling(5).mean().iloc[-1]
                ma20 = df[col_close].rolling(20).mean().iloc[-1]
                ma60 = df[col_close].rolling(60).mean().iloc[-1]
                ma_diff = (max(ma5, ma20, ma60) - min(ma5, ma20, ma60)) / min(ma5, ma20, ma60)
                
                # 2. 거래량 가뭄
                vol_dry = df[col_vol].iloc[-3:].mean() < df[col_vol].iloc[-20:].mean() * 0.6
                
                # 3. 수급 확인
                df_investor = stock.get_market_net_purchases_of_equities_by_ticker(start_date, target_date, ticker)
                is_buying = df_investor.loc[ticker, '기관합계'] > 0 or df_investor.loc[ticker, '외국인합계'] > 0
                
                if ma_diff < 0.03 and vol_dry and is_buying:
                    msg = f"💎 [폭발전야 포착] {name}\n🎯 밀집도: {ma_diff*100:.1f}%\n📉 거래량: 가뭄 (매집 의심)\n👤 수급: 기관/외인 매집"
                    send_telegram_msg(msg)
                    
    except Exception as e:
        print(f"상세 에러 내용: {e}")

if __name__ == "__main__":
    check_advanced_signals()
