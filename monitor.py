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
        
        # 💡 [지능형 로직] 이름표가 무엇이든 '거래대금'을 의미하는 단어가 포함된 칸을 찾습니다.
        money_cols = [c for c in df_market.columns if any(x in str(c) for x in ['거래대금', 'Amount', 'Value', 'Value_Sum'])]
        sort_col = money_cols[0] if money_cols else df_market.columns[min(5, len(df_market.columns)-1)]
        
        df_top = df_market.sort_values(by=sort_col, ascending=False).head(100)
        
        found_count = 0
        for ticker in df_top.index:
            try:
                name = stock.get_market_ticker_name(ticker)
                df = fdr.DataReader(ticker, (now - datetime.timedelta(days=60)).strftime('%Y-%m-%d'))
                
                if df is not None and len(df) > 30:
                    # 💡 [지능형 로직] 이름표 대신 데이터의 의미를 파악합니다.
                    # '종가' 후보들: Close, 종가, close
                    c_cols = [c for c in df.columns if any(x in str(c).lower() for x in ['close', '종가'])]
                    # '거래량' 후보들: Volume, 거래량, volume
                    v_cols = [c for c in df.columns if any(x in str(c).lower() for x in ['volume', '거래량'])]
                    
                    if not c_cols or not v_cols: 
                        # 이름표를 못 찾으면 칸 번호(index)로 강제 지정
                        c_col, v_col = df.columns[3], df.columns[4]
                    else:
                        c_col, v_col = c_cols[0], v_cols[0]

                    # 📈 이동평균선 계산
                    ma5 = df[c_col].rolling(5).mean().iloc[-1]
                    ma20 = df[c_col].rolling(20).mean().iloc[-1]
                    ma60 = df[c_col].rolling(60).mean().iloc[-1]
                    
                    ma_diff = (max(ma5, ma20, ma60) - min(ma5, ma20, ma60)) / min(ma5, ma20, ma60)
                    
                    # 📉 거래량 가뭄 확인
                    vol_avg = df[v_col].rolling(20).mean().iloc[-1]
                    vol_recent = df[v_col].iloc[-3:].mean()
                    
                    # 🎯 폭발전야 조건: 이평선 밀집(3% 이내) + 거래량 바닥(평균의 60% 이하)
                    if ma_diff < 0.03 and vol_recent < vol_avg * 0.6:
                        msg = f"💎 [폭발전야 포착] {name}\n🎯 밀집도: {ma_diff*100:.1f}%\n📉 거래량: 가뭄 (매집 의심)"
                        send_telegram_msg(msg)
                        found_count += 1
            except: continue # 한 종목이 에러나도 로봇은 멈추지 않습니다.
            
        print(f"분석 완료! 포착 종목: {found_count}개")
        
    except Exception as e:
        print(f"❌ 최종 에러 확인: {e}")

if __name__ == "__main__":
    check_market()
    
