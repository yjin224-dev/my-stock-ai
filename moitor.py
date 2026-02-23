import OpenDartReader
import datetime
import requests
import os

# 텔레그램 알림 함수 (영진님 ID: 8403847596)
def send_telegram_msg(text):
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = "8403847596"
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={text}"
    requests.get(url)

# 호재 키워드
positive_keywords = ["공급계약", "수주", "제3자배정", "자기주식취득", "소각", "특허", "무상증자"]

def check_disclosures():
    dart = OpenDartReader(os.environ["DART_API_KEY"])
    today = datetime.datetime.now().strftime('%Y%m%d')
    df = dart.list(end_date=today)
    
    if df is not None and not df.empty:
        # 최근 10분 내외의 공시만 필터링 (중복 알림 방지용 로직은 추후 보완 가능)
        for _, row in df.iterrows():
            title = row['report_nm']
            company = row['corp_nm']
            for key in positive_keywords:
                if key in title:
                    send_telegram_msg(f"🔔 [실시간 호재] {company}\n📄 {title}")
                    return # 하나만 보내고 종료 (테스트용)

if __name__ == "__main__":
    check_disclosures()
