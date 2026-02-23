import OpenDartReader
import datetime
import requests
import os

# 텔레그램 알림 함수 (영진님 고유 ID 적용)
def send_telegram_msg(text):
    # 깃허브 Secrets에서 토큰을 가져옵니다
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = "8403847596" # 영진님의 고유 ID
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={text}"
    requests.get(url)

# 호재 키워드 리스트
positive_keywords = ["공급계약", "수주", "제3자배정", "자기주식취득", "소각", "특허", "무상증자"]

def check_disclosures():
    try:
        # 깃허브 Secrets에서 DART 키를 가져옵니다
        dart = OpenDartReader(os.environ.get("DART_API_KEY"))
        today = datetime.datetime.now().strftime('%Y%m%d')
        df = dart.list(end_date=today)
        
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                title = row['report_nm']
                company = row['corp_nm']
                for key in positive_keywords:
                    if key in title:
                        msg = f"🔔 [24H 자동감시] {company}\n📄 {title}"
                        send_telegram_msg(msg)
                        print(f"{company} 알림 발송 완료")
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    check_disclosures()
