import streamlit as st
import monitor  # 우리가 방금 만든 monitor.py를 불러옵니다

# 1. 페이지 설정
st.set_page_config(page_title="Young-jin's Stock Monitor", layout="wide")

# 2. 제목 작성
st.title("📈 Young-jin's Power & Disclosure Monitor")
st.subheader("실시간 시장 데이터 분석 대시보드")

# 3. 사이드바 (필터링 등 메뉴)
st.sidebar.header("설정")
market_type = st.sidebar.selectbox("시장 선택", ["전체", "KOSPI", "KOSDAQ"])

# 4. 데이터 불러오기 및 출력
st.write("### 🏢 상장 종목 리스트")

# monitor.py에서 만든 함수를 실행해 데이터를 가져옵니다.
with st.spinner('데이터를 불러오는 중...'):
    df_stocks = monitor.get_stock_list()

# 시장 필터 적용
if market_type != "전체":
    df_stocks = df_stocks[df_stocks['Market'] == market_type]

# 화면에 표 출력
st.dataframe(df_stocks[['Code', 'Name', 'Market', 'Sector']].head(100))

st.success(f"현재 {market_type} 시장의 상위 100개 종목을 표시하고 있습니다.")
