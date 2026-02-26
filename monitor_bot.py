import os
import requests
import FinanceDataReader as fdr
import pandas as pd

# 1. 설정값 불러오기
# 토큰은 보안을 위해 환경변수에서 가져오고, 채팅 ID는 고정합니다.
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = "8403847596" 

def send_telegram(message):
    """텔레그램 메시지 전송 함수"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"메시지 전송 실패: {e}")

def detect_power():
    """세력(거래량) 포착 로직"""
    # 감시할 주요 종목 (원하시는 종목 코드로 자유롭게 변경하세요)
    # 005930(삼성전자), 000660(SK하이닉스), 086520(에코프로) 등
    target_stocks = ['005930', '000660', '086520', '005490', '035420']
    
    for code in target_stocks:
        try:
            # 최근 5일치 데이터 조회
            df = fdr.DataReader(code).tail(5)
            if len(df) < 2: continue
            
            # 현재 거래량과 전일 거래량 비교
            current_vol = df['Volume'].iloc[-1]
            prev_vol = df['Volume'].iloc[-2]
            current_price = df['Close'].iloc[-1]
            
            # 포착 기준: 현재 거래량이 전일 전체 거래량의 150%를 돌파했을 때
            if current_vol > (prev_vol * 1.5):
                # 종목명 가져오기 (선택 사항)
                msg = (f"🚨 [영진의 세력 포착]\n"
                       f"📦 종목코드: {code}\n"
                       f"💰 현재가: {current_price:,}원\n"
                       f"📈 현재 거래량: {current_vol:,}\n"
                       f"⚠️ 전일 대비 약 {int(current_vol/prev_vol*100)}% 폭발 중!")
                send_telegram(msg)
                print(f"{code} 포착 완료")
        except Exception as e:
            print(f"{code} 분석 중 오류: {e}")

if __name__ == "__main__":
    detect_power()
