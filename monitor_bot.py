import os
import datetime
import requests
import FinanceDataReader as fdr
from pykrx import stock
import OpenDartReader
from google import genai

# 1. 깃허브 Secrets 연결 (이미 설정하신 보안 키들)
DART_KEY = os.environ.get("DART_API_KEY")
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN")
AI_KEY = os.environ.get("GEMINI_API_KEY")
MY_CHAT_ID = "8403847596"  # 영진님의 텔레그램 고유 ID

# 2. 텔레그램 알림 함수
def send_tg(text):
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        payload = {'chat_id': MY_CHAT_ID, 'text': text}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"텔레그램 발송 실패: {e}")

# 3. 최신 AI 분석 함수 (Gemini 2.0 Flash)
def ask_ai(content):
    try:
        client = genai.Client(api_key=AI_KEY)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"주식 전문가로서 이 공시 제목이 호재인지 악재인지 판단해서 1문장으로 핵심만 요약해줘: {content}"
        )
        return response.text
    except:
        return "AI 분석 중..."

# 4. 실시간 감시 엔진 (1회 실행 모드)
def run_once():
    now = datetime.datetime.now()
    
    # 🧪 [핵심 추가] 봇이 정상 연결되었는지 확인하기 위한 즉시 알림
    test_msg = f"🤖 [영진 AI 비서] {now.strftime('%H:%M')}분석을 시작합니다. 장유에서 오늘도 화이팅하세요! 🦅"
    send_tg(test_msg)
    
    print(f"🚀 {now.strftime('%H:%M:%S')} - 분석 시작")

    # --- [섹션 1: 공시 감시] ---
    try:
        dart = OpenDartReader(DART_KEY)
        today = now.strftime('%Y%m%d')
        df_dart = dart.list(end_date=today)
        
        # 영진님이 설정한 핵심 호재 키워드
        keywords = ["공급계약", "수주", "제3자배정", "자기주식취득", "소각", "무상증자", "특허", "최대주주변경"]
        
        if df_dart is not None and not df_dart.empty:
            for _, row in df_dart.iterrows():
                title = row['report_nm']
                company = row['corp_nm']
                for key in keywords:
                    if key in title:
                        analysis = ask_ai(title)
                        msg = f"🔔 [호재 공시 포착]\n🏢 종목: {company}\n📄 내용: {title}\n🤖 AI 분석: {analysis}"
                        send_tg(msg)
    except Exception as e:
        print(f"공시 분석 중 에러: {e}")

    # --- [섹션 2: 세력 흔적 감시] ---
    try:
        # 거래대금 상위 종목 중 이상 징후 포착 (pykrx 사용)
        target_date = today
        df_price = stock.get_market_ohlcv(target_date, market="ALL")
        
        if df_price is None or df_price.empty:
            target_date = (now - datetime.timedelta(days=1)).strftime("%Y%m%d")
            df_price = stock.get_market_ohlcv(target_date, market="ALL")

        # 거래대금 상위 30개 중 급증 종목 탐색
        df_top = df_price.sort_values(by='거래대금', ascending=False).head(30)
        # (상세 로직은 영진님의 기존 전략에 맞춰 확장 가능합니다)
        
    except Exception as e:
        print(f"세력 분석 중 에러: {e}")

    print(f"✅ 분석 완료 및 종료")

if __name__ == "__main__":
    run_once()
