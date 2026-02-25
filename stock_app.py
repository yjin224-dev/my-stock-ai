import streamlit as st
import FinanceDataReader as fdr
from pykrx import stock
import datetime
import pandas as pd
import requests
import OpenDartReader
from streamlit_autorefresh import st_autorefresh

# 5분마다 자동 새로고침
st_autorefresh(interval=5 * 60 * 1000, key="fscounter")

def send_telegram_msg(text):
    try:
        token = st.secrets["TELEGRAM_TOKEN"]
        chat_id = "8403847596" 
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}"
        requests.post(url, json={'text': text}, timeout=10)
    except: pass

def check_disclosures():
    try:
        dart = OpenDartReader(st.secrets["DART_API_KEY"])
        today = datetime.datetime.now().strftime('%Y%m%d')
        df = dart.list(end_date=today)
        positive_keywords = ["공급계약", "수주", "제3자배정", "자기주식취득", "소각", "무상증자", "특허"]
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                title = row['report_nm']
                company = row['corp_nm']
                for key in positive_keywords:
                    if key in title:
                        msg = f"🔔 [호재 공시] {company}\n📄 {title}"
                        send_telegram_msg(msg)
                        st.sidebar.success(f"공시 알림 발송: {company}")
    except: pass

st.set_page_config(page_title="영진의 세력&공시 감시자", layout="wide")
st.title("🦅 영진의 실시간 세력 & 호재 포착기")

check_disclosures()

st.sidebar.header("⚙️ 세력 포착 설정")
vol_threshold = st.sidebar.slider("거래량 폭발 기준", 2.0, 10.0, 5.0)

if st.button('📡 전 종목 세력 흔적 탐색'):
    with st.spinner('시장 분석 중...'):
        now = datetime.datetime.now()
        target_date = now.strftime("%Y%m%d")
        df_price = stock.get_market_ohlcv(target_date, market="ALL")
        if df_price is None or df_price.empty:
            target_date = (now - datetime.timedelta(days=1)).strftime("%Y%m%d")
            df_price = stock.get_market_ohlcv(target_date, market="ALL")

        df_top = df_price.sort_values(by=df_price.columns[5], ascending=False).head(100)

        for ticker in df_top.index:
            try:
                name = stock.get_market_ticker_name(ticker)
                df = fdr.DataReader(ticker, (now - datetime.timedelta(days=40)).strftime('%Y-%m-%d'))
                if df is not None and len(df) > 20:
                    price_data, vol_data = df.iloc[:, 3], df.iloc[:, 4]
                    avg_vol, today_vol = vol_data.iloc[-16:-1].mean(), vol_data.iloc[-1]
                    if today_vol > avg_vol * vol_threshold and price_data.iloc[-1] > price_data.iloc[-2]:
                        st.write(f"### 🔥 [세력 포착] {name}")
            except: continue
