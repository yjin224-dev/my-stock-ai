import FinanceDataReader as fdr
from pykrx import stock
import datetime
import requests
import os
import sys

def send_msg(txt):
    try:
        token = os.environ.get("TELEGRAM_TOKEN")
        chat_id = "8403847596" # 영진님 ID
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}"
        requests.post(url, json={'text': txt}, timeout=10)
    except: pass

def run_logic():
    print("🚀 [영진님_완전_클린_버전] 한글 단어를 코드에서 100% 제거했습니다.")
    try:
        now = datetime.datetime.now()
        target_date = now.strftime("%Y%m%d")
        
        # 1. 시장 데이터 (이름표 대신 숫자로 정렬)
        df_m = stock.get_market_ohlcv(target_date, market="ALL")
        if df_m is None or df_m.empty:
            df_m = stock.get_market_ohlcv((now - datetime.timedelta(days=1)).strftime("%Y%m%d"), market="ALL")
        
        # 💡 [무적] 6번째 칸(Index 5)으로 정렬
        df_top = df_m.sort_values(by=df_m.columns[5], ascending=False).head(150)
        
        cnt = 0
        for ticker in df_top.index:
            try:
                name = stock.get_market_ticker_name(ticker)
                df = fdr.DataReader(ticker, (now - datetime.timedelta(days=100)).strftime('%Y-%m-%d'))
                
                if df is not None and len(df) > 30:
                    # 💡 [무적] 이름표 안 쓰고 위치(iloc)로만 데이터 추출
                    cp = df.iloc[:, 3] # 종가
                    vl = df.iloc[:, 4] # 거래량
                    
                    m5, m20, m60 = cp.rolling(5).mean().iloc[-1], cp.rolling(20).mean().iloc[-1], cp.rolling(60).mean().iloc[-1]
                    diff = (max(m5, m20, m60) - min(m5, m20, m60)) / min(m5, m20, m60)
                    
                    if diff < 0.04 and vl.iloc[-3:].mean() < vl.rolling(20).mean().iloc[-1] * 0.7:
                        amt = round(df_top.loc[ticker, df_m.columns[5]] / 100_000_000)
                        send_msg(f"💎 [포착] {name}\n💰 {amt}억 / 📉 밀집 {diff*100:.1f}%")
                        cnt += 1
            except: continue 
        print(f"✅ 분석 완료! {cnt}개 포착")
    except Exception as e:
        # 💡 몇 번째 줄에서 에러가 났는지 정확히 출력합니다.
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print(f"🆘 에러 발생 (라인 {exc_tb.tb_lineno}): {e}")

if __name__ == "__main__":
    run_logic()
