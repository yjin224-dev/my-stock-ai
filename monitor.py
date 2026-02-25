import FinanceDataReader as fdr
from pykrx import stock
import datetime
import requests
import os

def notify_telegram(message):
    try:
        token = os.environ.get("TELEGRAM_TOKEN")
        chat_id = "8403847596" # Your ID
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}"
        requests.post(url, json={'text': message}, timeout=10)
    except: pass

def scan_market():
    # 💡 이 문구가 로그에 떠야 영진님이 '완전 삭제'에 성공하신 겁니다!
    print("🚀 [NUCLEAR_RESET_SUCCESS] Running Clean English Version")
    
    try:
        now = datetime.datetime.now()
        target_date = now.strftime("%Y%m%d")
        
        # Get market data
        df_m = stock.get_market_ohlcv(target_date, market="ALL")
        if df_m is None or df_m.empty:
            df_m = stock.get_market_ohlcv((now - datetime.timedelta(days=1)).strftime("%Y%m%d"), market="ALL")
        
        # 💡 Use position (Index 5) for Trading Amount
        df_top = df_m.sort_values(by=df_m.columns[5], ascending=False).head(150)
        
        count = 0
        for ticker in df_top.index:
            try:
                name = stock.get_market_ticker_name(ticker)
                df = fdr.DataReader(ticker, (now - datetime.timedelta(days=100)).strftime('%Y-%m-%d'))
                
                if df is not None and len(df) > 30:
                    # 💡 Use position (iloc) for Price/Volume - NO KOREAN NAMES
                    # Index 3 = Close, Index 4 = Volume
                    cp = df.iloc[:, 3] 
                    vol = df.iloc[:, 4]     
                    
                    ma5, ma20, ma60 = cp.rolling(5).mean().iloc[-1], cp.rolling(20).mean().iloc[-1], cp.rolling(60).mean().iloc[-1]
                    diff = (max(ma5, ma20, ma60) - min(ma5, ma20, ma60)) / min(ma5, ma20, ma60)
                    
                    if diff < 0.035 and vol.iloc[-3:].mean() < vol.rolling(20).mean().iloc[-1] * 0.6:
                        amt = round(df_top.loc[ticker, df_m.columns[5]] / 100_000_000)
                        msg = f"🚩 [SQUEEZE] {name}\n💰 Amount: {amt}B KRW\n📈 Gap: {diff*100:.1f}%"
                        notify_telegram(msg)
                        count += 1
            except: continue 
        print(f"✅ Analysis Complete! Found: {count}")
    except Exception as e:
        print(f"🆘 Final Error Check: {e}")

if __name__ == "__main__":
    scan_market()
