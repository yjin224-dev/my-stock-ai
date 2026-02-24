import FinanceDataReader as fdr
from pykrx import stock
import datetime
import requests
import os

def send_msg(txt):
    try:
        token = os.environ.get("TELEGRAM_TOKEN")
        chat_id = "8403847596" # 영진님 ID
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}"
        requests.post(url, json={'text': txt}, timeout=10)
    except: pass

def run_smart_money_scan():
    print("🚀 [영진님_세력포착_모드] 분석을 시작합니다.")
    try:
        now = datetime.datetime.now()
        target_date = now.strftime("%Y%m%d")
        
        # 1. 시장 데이터 가져오기 (이름표 대신 숫자로만 접근)
        df_m = stock.get_market_ohlcv(target_date, market="ALL")
        if df_m is None or df_m.empty:
            target_date = (now - datetime.timedelta(days=1)).strftime("%Y%m%d")
            df_m = stock.get_market_ohlcv(target_date, market="ALL")
        
        # 💡 [iloc 마법] 6번째 칸(Index 5)인 '거래대금' 순으로 150개 선정
        df_top = df_m.sort_values(by=df_m.columns[5], ascending=False).head(150)
        
        found_cnt = 0
        for ticker in df_top.index:
            try:
                name = stock.get_market_ticker_name(ticker)
                df = fdr.DataReader(ticker, (now - datetime.timedelta(days=100)).strftime('%Y-%m-%d'))
                
                if df is not None and len(df) > 60:
                    # 💡 이름표 무시! 4번째(Index 3) = 종가, 5번째(Index 4) = 거래량
                    price = df.iloc[:, 3] 
                    volume = df.iloc[:, 4]     
                    
                    # 이동평균선 계산 (5, 20, 60일)
                    ma5, ma20, ma60 = price.rolling(5).mean().iloc[-1], price.rolling(20).mean().iloc[-1], price.rolling(60).mean().iloc[-1]
                    
                    # 밀집도 계산 (3% 이내 초밀집)
                    diff = (max(ma5, ma20, ma60) - min(ma5, ma20, ma60)) / min(ma5, ma20, ma60)
                    
                    # 거래량 가뭄 확인
                    vol_avg = volume.rolling(20).mean().iloc[-1]
                    vol_now = volume.iloc[-3:].mean()
                    
                    if diff < 0.03 and vol_now < vol_avg * 0.6:
                        money = round(df_top.loc[ticker, df_m.columns[5]] / 100_000_000)
                        msg = f"🚩 [세력매집] {name}\n💰 거래대금: {money}억\n📉 밀집도: {diff*100:.1f}%\n📊 상태: 에너지 응축중"
                        send_msg(msg)
                        found_cnt += 1
            except: continue 
        print(f"✅ 분석 완료! {found_cnt}개 포착")
    except Exception as e:
        print(f"🆘 오류 발생: {e}")

if __name__ == "__main__":
    run_smart_money_scan()
