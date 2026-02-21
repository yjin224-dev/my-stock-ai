import streamlit as st
import FinanceDataReader as fdr
from pykrx import stock
import datetime
import pandas as pd

st.set_page_config(page_title="제영진의 투자 비서", layout="wide")
st.title("📈 제영진님의 저평가 우량주 스캐너")

# 📅 날짜 설정 로직 업데이트 (주말/공휴일 대응)
now = datetime.datetime.now()
# 만약 오늘이 토요일(5)이나 일요일(6)이면 지난 금요일로 날짜 변경
if now.weekday() == 5: # 토요일
	now = now - datetime.timedelta(days=1)
elif now.weekday() == 6: # 일요일
	now = now - datetime.timedelta(days=2)
# 만약 아침 9시 전이라면 어제 날짜로 설정 (장이 열리기 전이므로)
elif now.hour < 9:
	now = now - datetime.timedelta(days=1)

target_date = now.strftime("%Y%m%d")
st.info(f"📅 분석 기준일: {now.strftime('%Y-%m-%d')} (주말/공휴일에는 가장 최근 영업일 데이터를 가져옵니다.)")

st.sidebar.header("🔍 필터 조건 설정")
max_price = st.sidebar.number_input("최대 주가 (원)", value=10000)
max_pbr = st.sidebar.slider("최대 PBR", 0.0, 2.0, 1.0) # PBR을 조금 높여서 1.0으로 기본값 변경

if st.button('🚀 실시간 종목 분석 시작'):
	with st.spinner('데이터를 분석 중입니다...'):
		try:
			# 1. 전 종목 기본 지표 가져오기
			df_fund = stock.get_market_fundamental(target_date, market="ALL")
			# 2. 전 종목 시세 가져오기
			df_price = stock.get_market_ohlcv(target_date, market="ALL")
            
			# 데이터 합치기
			result = pd.concat([df_price['종가'], df_fund], axis=1)
			result = result.reset_index()
			result.columns = ['티커', '현재가', 'BPS', 'PER', 'PBR', 'EPS', 'DIV', 'DPS']
            
			# 종목명 추가
			result['종목명'] = result['티커'].apply(lambda x: stock.get_market_ticker_name(x))

			# 🛠️ 영진님의 필터링 조건 적용
			# PBR은 0보다 커야 함 (자산 데이터가 있는 것만)
			filtered = result[
				(result['현재가'] <= max_price) & 
				(result['PBR'] > 0) & 
				(result['PBR'] <= max_pbr) &
				(result['EPS'] > 0) # EPS > 0 이면 흑자 기업입니다!
			]

			if not filtered.empty:
				st.success(f"조건에 맞는 종목 {len(filtered)}개를 찾았습니다!")
				# 보기 좋게 정리해서 보여주기
				final_df = filtered[['종목명', '현재가', 'PBR', 'PER']].sort_values(by='PBR')
				st.dataframe(final_df, use_container_width=True)
			else:
				st.warning(f"{target_date} 기준, 조건에 맞는 종목이 없습니다. 사이드바에서 PBR을 조금 높여보세요.")
                
		except Exception as e:
			st.error(f"오류가 발생했습니다: {e}")
