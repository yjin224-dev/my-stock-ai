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

def check_everything():
    try:
        dart = OpenDartReader(os.environ.get("DART_API_KEY"))
        now = datetime.datetime.now()
        
        # 1. 최근 영업일 데이터 확보 (데이터가 없으면 10일 전까지 뒤짐)
        target_date = now.strftime("%Y%m%d")
        df_market = None
        for i in range(0, 10):
            d = (now - datetime.timedelta(days=i)).strftime("%Y%m%d")
            try:
                df_market = stock.get_market_ohlcv(d, market="ALL")
                if not df_market.empty:
                    target_date = d
                    break
            except: continue

        if df_market is None or df_market.empty:
            print("데이터를 찾을 수 없습니다.")
            return

        # 2. 거래대금 상위 200개 추출 (이름표 대신 6번째 칸 위치 사용)
        # 보통 거래대금은 [시가,고가,저가,종가,거래량,거래대금] 순서의 6번째(index 5)입니다.
        df_top = df_market.sort_values(by=df_market.columns[min(5, len(df_market.columns)-1)], ascending=False).head(200)
        
        for ticker in df_top.index:
            try:
                name = stock.get_market_ticker_name(ticker)
                # fdr은 영어 이름표(Close, Volume)를 매우 안정적으로 줍니다.
                df = fdr.DataReader(ticker, (now - datetime.timedelta(days=100)).strftime('%Y-%m-%d'))
                
                if df is not None and len(df) > 60:
                    # 💡 이름표 대신 '칸 번호'로 데이터 추출 (안전장치)
                    close = df.iloc[:, 3] # 4번째 칸: 종가
                    vol = df.iloc[:, 4]   # 5번째 칸: 거래량
                    
                    # 📈 이평선 밀집 (4% 이내)
                    ma5, ma20, ma60 = close.rolling(5).mean().iloc[-1], close.rolling(20).mean().iloc[-1], close.rolling(60).mean().iloc[-1]
                    ma_diff = (max(ma5, ma20, ma60) - min(ma5, ma20, ma60)) / min(ma5, ma20, ma60)
                    
                    # 📉 거래량 바닥 확인
                    vol_dry = vol.iloc[-3:].mean() < vol.rolling(20).mean().iloc[-1] * 0.6
                    
                    if ma_diff < 0.04 and vol_dry:
                        # 🔍 공시 확인
                        dis = dart.list(ticker, start=target_date)
                        msg_dis = "🔔 공시: 없음"
                        if dis is not None and not dis.empty:
                            msg_dis = f"⚠️ 공시: {dis.iloc[0]['report_nm']}"

                        amt = round(df_top.loc[ticker, df_top.columns[5]] / 100_000_000)
                        msg = f"💎 [포착] {name}\n💰 거래대금: {amt}억\n📈 밀집도: {ma_diff*100:.1f}%\n{msg_dis}"
                        send_telegram_msg(msg)
            except: continue
        print("전체 분석 완료!")
    except Exception as e:
        print(f"최종 에러 상세: {e}")

if __name__ == "__main__":
    check_everything()
