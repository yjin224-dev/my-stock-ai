import FinanceDataReader as fdr
from pykrx import stock
import datetime
import requests
import os

def send_telegram_msg(text):
    try:
        token = os.environ.get("TELEGRAM_TOKEN")
        chat_id = "8403847596" # 영진님 ID
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}"
        requests.post(url, json={'text': text}, timeout=10)
    except: pass

def final_check():
    try:
        # 💡 [진단] 이 문구가 로그에 떠야 영진님이 수정한 코드가 진짜로 돌아가는 겁니다!
        print("🚀 [영진님_진짜_최종_버전_가동] 한글 이름표를 단 한 글자도 쓰지 않습니다.")
        
        now = datetime.datetime.now()
        target_date = now.strftime("%Y%m%d")
        
        # 시장 데이터 확보
        df_m = stock.get_market_ohlcv(target_date, market="ALL")
        if df_m is None or df_m.empty:
            df_m = stock.get_market_ohlcv((now - datetime.timedelta(days=1)).strftime("%Y%m%d"), market="ALL")
        
        # 💡 위치(6번째 칸)로 거래대금 정렬
        df_top = df_m.sort_values(by=df_m.columns[5], ascending=False).head(200)
        
        found_cnt = 0
        for ticker in df_top.index:
            try:
                name = stock.get_market_ticker_name(ticker)
                df = fdr.DataReader(ticker, (now - datetime.timedelta(days=100)).strftime('%Y-%m-%d'))
                
                if df is not None and len(df) > 30:
                    # 💡 [핵심] iloc[행, 열] - 이름표 대신 숫자로만 가져오기
                    # [0:시가, 1:고가, 2:저가, 3:종가, 4:거래량]
                    cp = df.iloc[:, 3] 
                    vol = df.iloc[:, 4]     
                    
                    ma5, ma20, ma60 = cp.rolling(5).mean().iloc[-1], cp.rolling(20).mean().iloc[-1], cp.rolling(60).mean().iloc[-1]
                    diff = (max(ma5, ma20, ma60) - min(ma5, ma20, ma60)) / min(ma5, ma20, ma60)
                    
                    if diff < 0.04 and vol.iloc[-3:].mean() < vol.rolling(20).mean().iloc[-1] * 0.7:
                        amt = round(df_top.loc[ticker, df_m.columns[5]] / 100_000_000)
                        msg = f"💎 [포착] {name}\n💰 거래대금: {amt}억\n📈 밀집도: {diff*100:.1f}%"
                        send_telegram_msg(msg)
                        found_cnt += 1
            except: continue 
        print(f"✅ 분석 완료! {found_cnt}개 포착")
    except Exception as e:
        print(f"🆘 최종 에러 확인: {e}")

if __name__ == "__main__":
    final_check()
