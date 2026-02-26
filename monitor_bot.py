import os
import requests
import FinanceDataReader as fdr
import pandas as pd

# 1. 설정값 (사용자님이 주신 정보 고정)
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = "8403847596" 

def send_telegram(message):
    """텔레그램 메시지 전송"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"전송 실패: {response.text}")
    except Exception as e:
        print(f"오류 발생: {e}")

def detect_power():
    # 텔레그램에 보낼 문구 구성
    # 감시 종목 리스트 (필요한 종목을 계속 추가하세요)
    target_stocks = {
        '005930': '삼성전자',
        '000660': 'SK하이닉스',
        '086520': '에코프로',
        '005490': 'POSCO홀딩스',
        '035420': 'NAVER'
    }
    
    for code, name in target_stocks.items():
        try:
            # 최근 2일 데이터 확인
            df = fdr.DataReader(code).tail(2)
            if len(df) < 2: continue
            
            curr_vol = df['Volume'].iloc[-1]
            prev_vol = df['Volume'].iloc[-2]
            curr_price = df['Close'].iloc[-1]
            
            # 세력 포착 기준: 거래량이 어제 전체의 1.3배(130%)를 넘었을 때
            if curr_vol > (prev_vol * 1.3):
                ratio = int((curr_vol / prev_vol) * 100)
                
                # 텔레그램으로 보낼 멋진 문구
                msg = (
                    f"🔥 *[영진의 세력 포착 알림]* 🔥\n"
                    f"--------------------------\n"
                    f"📦 *종목명*: {name} ({code})\n"
                    f"💰 *현재가*: {curr_price:,}원\n"
                    f"📈 *거래량*: {curr_vol:,}주\n"
                    f"⚡ *폭발력*: 전일 대비 {ratio}% 돌파!!\n"
                    f"--------------------------\n"
                    f"📢 *특이사항*: 대량 매수세 유입 포착!"
                )
                send_telegram(msg)
                
        except Exception as e:
            print(f"{name} 분석 중 에러: {e}")

if __name__ == "__main__":
    detect_power()
