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

def check_market_blind():
    try:
        now = datetime.datetime.now()
        target_date = now.strftime("%Y%m%d")
        
        # 1. 시장 전체 데이터 (오늘 데이터 없으면 최근 영업일로 자동 전환)
        df_market = stock.get_market_ohlcv(target_date, market="ALL")
        if df_market is None or df_market.empty:
            for i in range(1, 10):
                check_date = (now - datetime.timedelta(days=i)).strftime("%Y%m%d")
                df_market = stock.get_market_ohlcv(check_date, market="ALL")
                if not df_market.empty:
                    target_date = check_date
                    break
        
        print(f"[{now}] 분석 시작 (기준일: {target_date})")
        # 진단용: 실제로 어떤 이름표가 들어오는지 로그에 찍어둡니다.
        print(f"현재 데이터 이름표 리스트: {df_market.columns.tolist()}")

        # 💡 [무적 로직] 이름표 대신 '칸 번호'로만 정렬 (6번째 칸 = 거래대금)
        df_top = df_market.sort_values(by=df_market.columns[5], ascending=False).head(200)
        
        found_count = 0
        for ticker in df_top.index:
            try:
                name = stock.get_market_ticker_name(ticker)
                # 2. 개별 종목 60일 데이터 확보
                df = fdr.DataReader(ticker, (now - datetime.timedelta(days=100)).strftime('%Y-%m-%d'))
                
                if df is not None and len(df) > 30:
                    # 💡 [핵심] 글자 이름표를 완전히 빼버리고 숫자 위치(iloc)로만 데이터 추출
                    # 4번째 칸(Index 3) = 종가, 5번째 칸(Index 4) = 거래량
                    close_data = df.iloc[:, 3] 
                    vol_data = df.iloc[:, 4]   
                    
                    # 📈 이동평균선(MA) 계산
                    ma5 = close_data.rolling(5).mean().iloc[-1]
                    ma20 = close_data.rolling(20).mean().iloc[-1]
                    ma60 = close_data.rolling(60).mean().iloc[-1]
                    
                    # 이평선 밀집도 계산 수식
                    # $$ma\_diff = \frac{\max(ma5, ma20, ma60) - \min(ma5, ma20, ma60)}{\min(ma5, ma20, ma60)}$$
                    ma_diff = (max(ma5, ma20, ma60) - min(ma5, ma20, ma60)) / min(ma5, ma20, ma60)
                    
                    # 📉 거래량 확인 (최근 3일 평균이 20일 평균의 70% 이하)
                    vol_avg = vol_data.rolling(20).mean().iloc[-1]
                    vol_recent = vol_data.iloc[-3:].mean()
                    
                    if ma_diff < 0.04 and vol_recent < vol_avg * 0.7:
                        # 거래대금(6번째 칸) 데이터를 가져와 억 단위로 표시
                        amount_bill = round(df_top.loc[ticker, df_market.columns[5]] / 100_000_000)
                        msg = f"💎 [포착] {name}\n💰 거래대금: {amount_bill}억\n📈 밀집도: {ma_diff*100:.1f}%\n📉 상태: 거래량 가뭄"
                        send_telegram_msg(msg)
                        found_count += 1
            except: continue 

        print(f"✅ 분석 완료! 포착 종목: {found_count}개")
        
    except Exception as e:
        print(f"❌ 최종 에러 발생: {e}")

if __name__ == "__main__":
    check_market_blind()
