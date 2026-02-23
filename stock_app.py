import streamlit as st
import FinanceDataReader as fdr
from pykrx import stock
import datetime
import pandas as pd
import requests
from streamlit_autorefresh import st_autorefresh

# 5분마다 자동 새로고침 (장유 사무실에서 폰만 켜두면 자동 감시!)
st_autorefresh(interval=5 * 60 * 1000, key="fscounter")

# 텔레그램 알림 함수 (영진님 ID: 8403847596)
def send_telegram_msg(text):
    try:
        token = st.secrets["TELEGRAM_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={text}"
        requests.get(url)
    except:
        pass

st.set_page_config(page_title="제영진의 투자 비서", layout="wide")
st.title("🚀 영진의 세력 포착 & 모멘텀 스캐너")

# sidebar 설정
st.sidebar.header("🔍 세력 매집 조건")
vol_factor = st.sidebar.slider("거래량 폭발 기준 (평균 대비)", 2.0, 5.0, 3.0)
max_pbr = st.sidebar.slider("최대 PBR", 0.0, 1.5, 0.8) # 종목이 너무 안 나오면 0.8 정도로 올려보세요!

if st.button('📡 세력 흔적 탐색 시작'):
    with st.spinner('전 종목 거래량 및 차트 분석 중...'):
        now = datetime.datetime.now()
        target_date = now.strftime("%Y%m%d")
        
        # 1. 저평가 종목 기본 추출
        df_fund = stock.get_market_fundamental(target_date, market="ALL")
        df_price = stock.get_market_ohlcv(target_date, market="ALL")
        result = pd.concat([df_price['종가'], df_price['거래량'], df_fund['PBR']], axis=1)
        
        # 기본 필터: PBR 0.8 이하 저평가주 대상
        cond = (result['PBR'] > 0) & (result['PBR'] <= max_pbr)
        candidates = result[cond].index.tolist()
        
        hit_list = []
        for ticker in candidates[:50]: # 상위 50개 정밀 분석
            name = stock.get_market_ticker_name(ticker)
            # 최근 20일 데이터로 평균 거래량 계산
            df = fdr.DataReader(ticker, (now - datetime.timedelta(days=40)).strftime('%Y-%m-%d'))
            
            if len(df) > 20:
                avg_vol = df['Volume'].iloc[-21:-1].mean() # 최근 20일 평균 거래량
                today_vol = df['Volume'].iloc[-1]
                
                # 📊 거래량 폭발 조건 (세력 개입 의심)
                if today_vol > avg_vol * vol_factor:
                    # 📈 골든크로스까지 겹쳤는지 확인
                    ma5 = df['Close'].rolling(5).mean()
                    ma20 = df['Close'].rolling(20).mean()
                    
                    status = "🔥 거래량 폭발!"
                    if ma5.iloc[-1] > ma20.iloc[-1] and ma5.iloc[-2] <= ma20.iloc[-2]:
                        status = "🧨 세력 진입 + 골든크로스!!"
                    
                    hit_list.append(f"{name} ({status})")
                    # 🔔 즉시 알림
                    send_telegram_msg(f"📢 [세력 포착] {name}\n현재가: {df['Close'].iloc[-1]:,}원\n상태: {status}\n거래량: 평소 대비 {today_vol/avg_vol:.1f}배!")

        if hit_list:
            for hit in hit_list:
                st.success(hit)
        else:
            st.warning("현재 세력의 흔적이 포착된 저평가 종목이 없습니다. 조건을 살짝 늦춰보세요!")
