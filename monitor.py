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

def run_elite_logic():
    try:
        # 💡 내가 보낸 최신 코드가 맞는지 확인용 도장
        print("🚀 [영진님_최종_마스터키_가동] 이름표 단어 싹 뺐습니다.")
        
        now = datetime.datetime.now()
        target_date = now.strftime("%Y%m%d")
        
        df_market = stock.get_market_ohlcv(target_date, market="ALL")
        if df_market is None or df_market.empty:
            df_market = stock.get_market_ohlcv((now - datetime.timedelta(days=1)).strftime("%Y%m%d"), market="ALL")
        
        # 💡 위치(6번째 칸, index 5)로 거래대금 정렬
        df_top = df_market.sort_values(by=df_market.columns[5], ascending=False).head(200)
        
        found_count = 0
        for ticker in df_top.index:
            try:
                name = stock.get_market_ticker_name(ticker)
                df = fdr.DataReader(ticker, (now - datetime.timedelta(days=100)).strftime('%Y-%m-%d'))
                
                if df is not None and len(df) > 30:
                    # 💡 iloc[행, 열]을 사용하여 4번째(Index 3)가 '종가', 5번째(Index 4)가 '거래량'
                    close_p = df.iloc[:, 3] 
                    vol = df.iloc[:, 4]     
                    
                    ma5 = close_p.rolling(5).mean().iloc[-1]
                    ma20 = close_p.rolling(20).mean().iloc[-1]
                    ma60 = close_p.rolling(60).mean().iloc[-1]
                    
                    # 이평선 밀집도 계산 수식:
                    # $$ma\_diff = \frac{\max(ma5, ma20, ma60) - \min(ma5, ma20, ma60)}{\min(ma5, ma20, ma60)}$$
                    ma_diff = (max(ma5, ma20, ma60) - min(ma5, ma20, ma60)) / min(ma5, ma20, ma60)
                    
                    # 🎯 조건: 밀집도 4% 이내 & 거래량 가뭄
                    if ma_diff < 0.04 and vol.iloc[-3:].mean() < vol.rolling(20).mean().iloc[-1] * 0.7:
                        amount = round(df_top.loc[ticker, df_market.columns[5]] / 100_000_000)
                        msg = f"💎 [포착] {name}\n💰 거래대금: {amount}억\n📈 밀집도: {ma_diff*100:.1f}%"
                        send_telegram_msg(msg)
                        found_count += 1
            except: continue 
        print(f"✅ 분석 완료! {found_count}개 포착")
    except Exception as e:
        print(f"🆘 최종 에러 확인: {e}")

if __name__ == "__main__":
    run_elite_logic()
