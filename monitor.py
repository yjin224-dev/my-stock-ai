import FinanceDataReader as fdr
from pykrx import stock
import datetime
import requests
import os

def notify_telegram(message):
    try:
        token = os.environ.get("TELEGRAM_TOKEN")
        chat_id = "8403847596" # 영진님 ID
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}"
        requests.post(url, json={'text': message}, timeout=10)
    except: pass

def scan_market():
    # 💡 이 문구가 로그에 떠야 '완전 삭제' 후 '새로 입력'에 성공한 것입니다!
    print("🚀 [FINAL_BULLETPROOF_SCAN] No labels, only numbers.")
    
    try:
        now = datetime.datetime.now()
        target_date = now.strftime("%Y%m%d")
        
        # 1. 시장 전체 데이터 확보 (오늘 데이터 없으면 최근 영업일로 자동 보정)
        df_m = stock.get_market_ohlcv(target_date, market="ALL")
        if df_m is None or df_m.empty:
            df_m = stock.get_market_ohlcv((now - datetime.timedelta(days=1)).strftime("%Y%m%d"), market="ALL")
        
        # 💡 [iloc] 이름표 대신 6번째 칸(Index 5)인 '거래대금' 순으로 정렬
        df_top = df_m.sort_values(by=df_m.columns[5], ascending=False).head(150)
        
        count = 0
        for ticker in df_top.index:
            try:
                name = stock.get_market_ticker_name(ticker)
                df = fdr.DataReader(ticker, (now - datetime.timedelta(days=100)).strftime('%Y-%m-%d'))
                
                if df is not None and len(df) > 30:
                    # 💡 [핵심] 이름표 완전 무시! 위치(iloc)로 데이터 강제 추출
                    # Index 3 = 종가, Index 4 = 거래량
                    price_data = df.iloc[:, 3] 
                    volume_data = df.iloc[:, 4]     
                    
                    # 📈 이동평균선(5, 20, 60일) 계산
                    ma5 = price_data.rolling(5).mean().iloc[-1]
                    ma20 = price_data.rolling(20).mean().iloc[-1]
                    ma60 = price_data.rolling(60).mean().iloc[-1]
                    
                    # 📐 이평선 밀집도(Squeeze) 계산
                    # $$diff = \frac{\max(ma5, ma20, ma60) - \min(ma5, ma20, ma60)}{\min(ma5, ma20, ma60)}$$
                    diff = (max(ma5, ma20, ma60) - min(ma5, ma20, ma60)) / min(ma5, ma20, ma60)
                    
                    # 📉 세력 매집 시그널: 밀집도 3.5% 이내 & 거래량 가뭄(평소의 60% 이하)
                    recent_vol = volume_data.iloc[-3:].mean()
                    avg_vol = volume_data.rolling(20).mean().iloc[-1]
                    
                    if diff < 0.035 and recent_vol < avg_vol * 0.6:
                        # 💰 거래대금(6번째 칸) 추출 및 억 단위 변환
                        amt = round(df_top.loc[ticker, df_m.columns[5]] / 100_000_000)
                        msg = f"💎 [포착] {name}\n💰 거래대금: {amt}억\n📈 밀집도: {diff*100:.1f}%\n📊 상태: 에너지 응축 중"
                        notify_telegram(msg)
                        count += 1
            except: continue 
        print(f"✅ Analysis Complete! Found: {count}")
    except Exception as e:
        print(f"🆘 Final Error Check: {e}")

if __name__ == "__main__":
    scan_market()
