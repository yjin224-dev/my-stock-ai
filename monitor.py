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
        chat_id = "8403847596" # 영진님 텔레그램 고유 ID
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={text}"
        requests.get(url, timeout=10)
    except: pass

def fix_cols(df):
    if df is None or df.empty: return None
    # 모든 컬럼명을 대문자로 통일하여 에러를 원천 차단합니다.
    df.columns = [str(c).upper() for c in df.columns]
    mapping = {'종가': 'CLOSE', '거래량': 'VOLUME', '거래대금': 'AMOUNT'}
    new_cols = {col: v for col in df.columns for k, v in mapping.items() if k in col}
    df.rename(columns=new_cols, inplace=True)
    return df

def run_final_check():
    try:
        dart = OpenDartReader(os.environ.get("DART_API_KEY"))
        now = datetime.datetime.now()
        
        # 🔍 1. 데이터가 있는 가장 최근 영업일을 찾습니다.
        df_market = None
        target_date = ""
        for i in range(0, 10):
            d = (now - datetime.timedelta(days=i)).strftime("%Y%m%d")
            df_market = stock.get_market_ohlcv(d, market="ALL")
            if not df_market.empty:
                target_date = d
                break
        
        if df_market is None or df_market.empty:
            print("❌ 데이터를 가져올 수 있는 영업일을 찾지 못했습니다.")
            return

        print(f"✅ 분석 기준일: {target_date}")
        df_market = fix_cols(df_market)
        
        # 🔍 2. 거래대금 상위 300개 중 500억 이상 터진 종목 추출
        df_top = df_market[df_market['AMOUNT'] >= 50_000_000_000].sort_values(by='AMOUNT', ascending=False).head(300)
        
        found_count = 0
        for ticker in df_top.index:
            try:
                name = stock.get_market_ticker_name(ticker)
                df = fdr.DataReader(ticker, (now - datetime.timedelta(days=120)).strftime('%Y-%m-%d'))
                df = fix_cols(df)
                
                if df is not None and len(df) > 60 and 'CLOSE' in df.columns:
                    close = df['CLOSE']
                    # 📈 이평선 밀집도 계산
                    ma5, ma20, ma60 = close.rolling(5).mean().iloc[-1], close.rolling(20).mean().iloc[-1], close.rolling(60).mean().iloc[-1]
                    ma_diff = (max(ma5, ma20, ma60) - min(ma5, ma20, ma60)) / min(ma5, ma20, ma60)
                    
                    # 📉 거래량 바닥 (매집 신호)
                    vol_dry = df['VOLUME'].iloc[-3:].mean() < df['VOLUME'].rolling(20).mean().iloc[-1] * 0.7
                    
                    if ma_diff < 0.04 and vol_dry:
                        # 🔍 공시 확인 (오늘 자 주요 공시)
                        dis = dart.list(ticker, start=target_date)
                        dis_msg = "🔔 공시: 없음"
                        if dis is not None and not dis.empty:
                            dis_msg = f"⚠️ 공시: {dis.iloc[0]['report_nm']}"

                        amt_bill = round(df_top.loc[ticker, 'AMOUNT'] / 100_000_000)
                        msg = f"💎 [정예 포착] {name}\n💰 거래대금: {amt_bill}억\n📈 밀집도: {ma_diff*100:.1f}%\n{dis_msg}"
                        send_telegram_msg(msg)
                        found_count += 1
            except: continue
            
        print(f"🏁 분석 완료! 포착 종목: {found_count}개")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    run_final_check()
