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
    # Diagnostic message to confirm this version is running
    print("🚀 [English_Positional_Mode] Starting analysis...")
    
    try:
        now = datetime.datetime.now()
        target_date = now.strftime("%Y%m%d")
        
        # Get market data (Auto-correct for weekends)
        df_m = stock.get_market_ohlcv(target_date, market="ALL")
        if df_m is None or df_m.empty:
            df_m = stock.get_market_ohlcv((now - datetime.timedelta(days=1)).strftime("%Y%m%d"), market="ALL")
        
        # 💡 [iloc] Sort by 6th column (Trading Amount) - Index 5
        df_top = df_m.sort_values(by=df_m.columns[5], ascending=False).head(150)
        
        count = 0
        for ticker in df_top.index:
            try:
                name = stock.get_market_ticker_name(ticker)
                df = fdr.DataReader(ticker, (now - datetime.timedelta(days=100)).strftime('%Y-%m-%d'))
                
                if df is not None and len(df) > 30:
                    # 💡 [iloc] 4th col (Index 3) = Close, 5th col (Index 4) = Volume
                    cp = df.iloc[:, 3] 
                    vol = df.iloc[:, 4]     
                    
                    # Calculate Moving Averages
                    ma5, ma20, ma60 = cp.rolling(5).mean().iloc[-1], cp.rolling(20).mean().iloc[-1], cp.rolling(60).mean().iloc[-1]
                    
                    # Squeeze Formula:
                    # $$diff = \frac{\max(ma5, ma20, ma60) - \min(ma5, ma20, ma60)}{\min(ma5, ma20, ma60)}$$
                    diff = (max(ma5, ma20, ma60) - min(ma5, ma20, ma60)) / min(ma5, ma20, ma60)
                    
                    # Volume Condition: Recent 3-day avg < 20-day avg * 0.6 (Low Volume)
                    if diff < 0.035 and vol.iloc[-3:].mean() < vol.rolling(20).mean().iloc[-1] * 0.6:
                        # 6th col = Trading Amount (Convert to 100M KRW)
                        amt = round(df_top.loc[ticker, df_m.columns[5]] / 100_000_000)
                        msg = f"🚩 [SQUEEZE] {name}\n💰 Amount: {amt}B KRW\n📈 Gap: {diff*100:.1f}%\n📊 Status: Ready to Launch"
                        notify_telegram(msg)
                        count += 1
            except: continue 
        print(f"✅ Job Done! Found: {count}")
    except Exception as e:
        print(f"🆘 Error Details: {e}")

if __name__ == "__main__":
    scan_market()
