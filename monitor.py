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
        
        # 1. 시장 전체 데이터 가져오기
        df_price = stock.get_market_ohlcv(target_date, market="ALL")
        df_top = df_price.sort_values(by='거래대금', ascending=False).head(100)
        
        for ticker in df_top.index:
            name = stock.get_market_ticker_name(ticker)
            # fdr은 보통 영어 컬럼('Close')을 반환합니다.
            df = fdr.DataReader(ticker, (now - datetime.timedelta(days=60)).strftime('%Y-%m-%d'))
            
            if df is not None and len(df) > 30:
                # 🔍 [에러 해결 핵심] 한글/영어 컬럼명 자동 매칭
                # 'Close'가 없으면 '종가'를 사용하고, 'Volume'이 없으면 '거래량'을 사용합니다.
                c_name = 'Close' if 'Close' in df.columns else '종가'
                v_name = 'Volume' if 'Volume' in df.columns else '거래량'
                
                # 데이터가 정상인지 한 번 더 확인
                if c_name not in df.columns: continue

                # 2. 이평선 밀집도 계산
                ma5 = df[c_name].rolling(5).mean().iloc[-1]
                ma20 = df[c_name].rolling(20).mean().iloc[-1]
                ma60 = df[c_name].rolling(60).mean().iloc[-1]
                ma_diff = (max(ma5, ma20, ma60) - min(ma5, ma20, ma60)) / min(ma5, ma20, ma60)
                
                # 3. 거래량 가뭄 확인 (최근 3일 평균이 20일 평균의 60% 이하)
                vol_dry = df[v_name].iloc[-3:].mean() < df[v_name].iloc[-20:].mean() * 0.6
                
                # 4. 수급 확인 (기관이나 외국인이 사고 있는지)
                df_investor = stock.get_market_net_purchases_of_equities_by_ticker(start_date, target_date, ticker)
                is_buying = False
                if ticker in df_investor.index:
                    is_buying = df_investor.loc[ticker, '기관합계'] > 0 or df_investor.loc[ticker, '외국인합계'] > 0
                
                # 🎯 모든 조건 충족 시 알림
                if ma_diff < 0.03 and vol_dry and is_buying:
                    msg = f"💎 [폭발전야 포착] {name}\n🎯 밀집도: {ma_diff*100:.1f}%\n📉 거래량: 가뭄 (매집 의심)\n👤 수급: 기관/외인 매집 중"
                    send_telegram_msg(msg)
                    
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    check_advanced_signals()
