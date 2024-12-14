# 🙋‍♂️ 2024-1-SCS403-Teamirum-S4

<div><img src="https://capsule-render.vercel.app/api?type=waving&color=0:99cc99,100:009630&height=200&section=header&text=Teamirum&fontSize=90" /></div>


| 구분 | 성명 | 학번 | 소속학과 | 연계전공 | 이메일 |
| --- | --- | --- | --- | --- | --- |
| 팀장 | 민예지 | 2019112481 | 경영정보학과 | 융합소프트웨어 | jjrmmee@gmail.com |
| 팀원 | 김명하 | 2019110359 | 산업시스템공학과 | 융합소프트웨어 | khmyung3041@gmail.com |
| 팀원 | 윤석규 | 2019111770 | 통계학과 | 융합소프트웨어 | kehahahaaaa@gmail.com |
| 팀원 | 전병현 | 2019111770 | 산업시스템공학과 | 융합소프트웨어 | qudgus0522@gmail.com  |
- 지도교수: 동국대학교 SW교육원 신연순 교수님, 박효순 교수님

## ❗ 서비스 소개
본 서비스는 AI 기반의 개인 맞춤형 보험 추천 서비스입니다.  
복잡한 보험 상품 선택의 어려움을 해소하고, 사용자에게 최적의 보험 상품을 추천하여 시간과 노력을 절약하는 데 목표를 두고 있습니다.

## 📢 기능 설명
### 1. 개인 맞춤형 보험 상품 추천 기능
* **정보 수집:**  이름, 나이, 성별, 연락처, 이메일 주소 등 기본 정보와 세부적인 정보를 입력받음.
* **AI 기반 추천:**  입력된 정보를 바탕으로 AI 알고리즘이 사용자에게 최적의 보험 상품을 추천. 추천 결과는 보험 상품 상세 정보, 보장 내용, 약관 등을 포함하여 사용자가 쉽게 이해할 수 있도록 제공. TOP4 보험사 상품 비교 기능을 통해 사용자는 다양한 상품을 손쉽게 비교 분석할 수 있음. 



### 2. 챗봇 기능
* **자연어 처리 기반 질의응답:**  사용자 질문에 대한 자연스러운 답변 제공.
* **시뮬레이션 기능:**  보험료, 보험금 등을 계산하는 시뮬레이션 기능과 상담 챗봇 기능을 제공하여 사용자의 보험 선택 결정을 지원. 

## 3. 실행 방법
- IDE 터미널 streamlit과 백엔드 각각 총 2개를 열어야함
- 프론트엔드는 파일을 직접 실행시켜야 함

### 3-0. 가상환경 생성 (최초 1회만, 사용하는 가상환경이 있는 경우 생략 가능)
    windows : python -m venv {가상 환경 이름}
    mac : python3 -m venv {가상 환경 이름}

    windows : source venv/Scripts/activate
    mac : source venv/bin/activate

### 3-1. 라이브러리 설치
    pip install -r requirements.txt

### 3-2. 백엔드 서버 실행
    cd BE (2024-2-SCS4031-Teamirum-4\BE 경로에서 실행해야함)
    python manage.py runserver

### 3-3. streamlit 서버 실행
    cd AI/Simulation (2024-2-SCS4031-Teamirum-4\AI\Simulation 경로에서 실행해야함)
    streamlit run chatbot.py

### 3-4. 프론트엔드 파일 열기
    2024-2-SCS4031-Teamirum-4\FE\pages에 있는 1.main.html 파일 열고 진행


