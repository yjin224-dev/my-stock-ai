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
        
        # 1. 최근 영업일 데이터 확보 (오늘 장이 안 열렸으면 이전 날짜로)
        df_market = stock.get_market_ohlcv(target_date, market="ALL")
        if df_market is None or df_market.empty:
            for i in range(1, 10):
                check_date = (now - datetime.timedelta(days=i)).strftime("%Y%m%d")
                df_market = stock.get_market_ohlcv(check_date, market="ALL")
                if df_market is not None and not df_market.empty:
                    target_date = check_date
                    break

        print(f"[{now}] 분석 기준일: {target_date}")
        
        # 💡 [보안 로직] 이름표가 무엇이든 '거래대금' 칸을 지능적으로 찾습니다.
        money_col = [c for c in df_market.columns if '거래대금' in c or 'Amount' in c or 'Value' in c]
        if not money_col:
            # 이름표를 못 찾으면 '6번째 칸'을 거래대금으로 가정 (데이터 표준 순서)
            sort_target = df_market.columns[min(5, len(df_market.columns)-1)]
        else:
            sort_target = money_col[0]

        df_top = df_market.sort_values(by=sort_target, ascending=False).head(100)
        
        found_count = 0
        for ticker in df_top.index:
            try:
                name = stock.get_market_ticker_name(ticker)
                df = fdr.DataReader(ticker, (now - datetime.timedelta(days=60)).strftime('%Y-%m-%d'))
                
                if df is not None and len(df) > 30:
                    # 💡 [보안 로직] '종가'와 '거래량' 이름표를 유연하게 찾습니다 (대소문자, 한글 포함)
                    c_cols = [c for c in df.columns if any(x in c for x in ['Close', '종가', 'close'])]
                    v_cols = [c for c in df.columns if any(x in c for x in ['Volume', '거래량', 'volume'])]
                    
                    if not c_cols or not v_cols: continue
                    
                    c_col, v_col = c_cols[0], v_cols[0]

                    # 📈 이평선 밀집도 계산
                    ma5 = df[c_col].rolling(5).mean().iloc[-1]
                    ma20 = df[c_col].rolling(20).mean().iloc[-1]
                    ma60 = df[c_col].rolling(60).mean().iloc[-1]
                    ma_diff = (max(ma5, ma20, ma60) - min(ma5, ma20, ma60)) / min(ma5, ma20, ma60)
                    
                    # 📉 거래량 가뭄 확인
                    vol_avg = df[v_col].iloc[-20:].mean()
                    vol_recent = df[v_col].iloc[-3:].mean()
                    
                    # 🎯 폭발전야 조건: 밀집도 3% 이내 + 거래량 가뭄
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
