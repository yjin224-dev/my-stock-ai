import streamlit as st
import FinanceDataReader as fdr
from pykrx import stock
import datetime
import pandas as pd
import requests

# 텔레그램 알림 함수
def send_telegram_msg(text):
    try:
        token = st.secrets["TELEGRAM_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={text}"
        requests.get(url)
    except:
        pass

st.set_page_config(page_title="제영진의 투자 비서", layout="wide")
st.title("🚀 제영진의 상승 모멘텀 스캐너")

# 날짜 설정
now = datetime.datetime.now()
if now.weekday() >= 5: # 주말이면 금요일로
    now = now - datetime.timedelta(days=(now.weekday()-4))
target_date = now.strftime("%Y%m%d")

st.sidebar.header("🔍 필터 조건")
max_price = st.sidebar.number_input("최대 주가", value=10000)
max_pbr = st.sidebar.slider("최대 PBR", 0.0, 1.5, 0.8)

if st.button('📈 상승 모멘텀 분석 시작'):
    with st.spinner('차트 분석 중...'):
        # 1. 기본 저평가 종목 추출
        df_fund = stock.get_market_fundamental(target_date, market="ALL")
        df_price = stock.get_market_ohlcv(target_date, market="ALL")
        result = pd.concat([df_price['종가'], df_fund['PBR'], df_fund['EPS']], axis=1)
        
        # 필터링
        cond = (result['종가'] <= max_price) & (result['PBR'] > 0) & (result['PBR'] <= max_pbr) & (result['EPS'] > 0)
        candidates = result[cond].index.tolist()
        
        hit_list = []
        for ticker in candidates[:30]: # 상위 30개만 정밀 분석
            name = stock.get_market_ticker_name(ticker)
            # 최근 20일 시세 가져오기
            df = fdr.DataReader(ticker, (now - datetime.timedelta(days=40)).strftime('%Y-%m-%d'))
            
            if len(df) > 20:
                ma5 = df['Close'].rolling(5).mean()
                ma20 = df['Close'].rolling(20).mean()
                
                # 📈 골든크로스 포착 (5일선이 20일선을 돌파)
                if ma5.iloc[-1] > ma20.iloc[-1] and ma5.iloc[-2] <= ma20.iloc[-2]:
                    hit_list.append(name)
                    # 🔔 즉시 알림 발송!
                    send_telegram_msg(f"📢 [모멘텀 포착] {name}\n현재가: {df['Close'].iloc[-1]:,}원\n골든크로스 발생! 확인해보세요.")

        if hit_list:
            st.success(f"오늘의 상승 예견 종목: {', '.join(hit_list)}")
        else:
            st.warning("현재 모멘텀이 포착된 저평가 종목이 없습니다.")
