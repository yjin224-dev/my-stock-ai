# 📈 Young-jin's Power & Disclosure Monitor

주식 시장의 핵심적인 흐름(**Power**)과 기업의 주요 **공시(Disclosure)** 정보를 실시간으로 추적하고 분석하는 AI 기반 모니터링 도구입니다.

## ✨ 주요 기능 (Key Features)
- **실시간 공시 모니터링:** 놓치기 쉬운 중요 공시 정보를 즉각적으로 포착합니다.
- **수급 및 세력(Power) 분석:** 거래량과 가격 변동을 분석하여 시장의 에너지를 파악합니다.
- **데이터 시각화:** 분석된 데이터를 직관적인 대시보드 형태로 제공합니다. (진행 중)
- **AI 기반 인사이트:** 수집된 정보를 바탕으로 주가에 미칠 영향을 분석합니다.

## 🛠 기술 스택 (Tech Stack)
- **Language:** ![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=Python&logoColor=white)
- **Framework:** (예: Streamlit, Flask 등 사용하는 프레임워크가 있다면 추가)
- **Database:** (추후 데이터 저장 시 추가)

## 🚀 시작하기 (Getting Started)

### 1. 환경 설정
프로젝트에 필요한 라이브러리를 설치합니다.
```bash
pip install -r requirements.txt

# 데이터 분석 및 조작
pandas
numpy

# 주가 데이터 가져오기 (한국 및 해외)
yfinance
finance-datareader

# 대한민국 공시 시스템(DART) 연결
dart-fss

# 웹 대시보드 만들기 (추천)
streamlit

# AI 분석 (Gemini API 사용 시)
google-generativeai
