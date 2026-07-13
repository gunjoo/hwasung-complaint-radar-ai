# 화성 민원 레이더 AI

본 데이터는 공모전 시연용 가상 데이터이며, 실제 국민신문고·민원 데이터와 무관함.

화성 민원 레이더 AI는 국민신문고를 대체하는 서비스가 아닙니다. 민원 접수 이후 단계에서 가상 생활불편 민원을 분석해 반복 민원, 위험 조기감지 참고 지표, 담당자 조치카드, 시민 답변 표준문안, 예방 알림을 보여주는 웹 브라우저용 시연 프로토타입입니다.

## 주요 기능

- 대시보드: 전체 민원 건수, 분야별·긴급도별·시설별 건수, 반복 키워드 TOP 10, 예방 알림 카드
- 민원 AI 분석: 사용자가 입력한 문장을 키워드 기반 규칙으로 분석
- 반복 민원 레이더: 샘플 민원 50건 기반 반복 이슈와 주의 필요 항목 표시
- 담당자 조치카드: 유형별 확인사항, 시민 답변, 내부 검토 메모 분리 표시
- 솔루션 소개: 비대체 원칙과 데이터 안전 원칙 안내

## 기술 스택

- Python
- Streamlit
- Pandas
- Plotly
- CSV 기반 샘플 데이터

## 로컬 실행 방법

```powershell
cd hwasung-complaint-radar-ai
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m streamlit run app.py
```

Streamlit을 처음 실행할 때 이메일 입력 안내가 나오면 빈칸으로 `Enter`를 눌러도 됩니다.

같은 네트워크의 다른 기기에서 접속하려면 다음처럼 실행합니다.

```powershell
python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

## Streamlit Community Cloud 배포 방법

1. GitHub에 새 저장소를 만들고 이 프로젝트 폴더의 파일을 업로드합니다.
2. 저장소 루트에 `app.py`, `requirements.txt`, `data/sample_complaints.csv`, `services/analyzer.py`가 있는지 확인합니다.
3. Streamlit Community Cloud에 로그인합니다.
4. `New app`을 선택하고 GitHub 저장소를 연결합니다.
5. 배포 설정에서 `Main file path`를 `app.py`로 지정합니다.
6. `Deploy`를 누르면 `requirements.txt` 기준으로 패키지가 설치되고 앱이 실행됩니다.

이 프로토타입은 API Key를 사용하지 않습니다. 향후 API를 붙일 경우 공개 저장소에 키를 올리지 말고 Streamlit Secrets 또는 환경변수를 사용해야 합니다.

## 프로젝트 구조

```text
hwasung-complaint-radar-ai/
├─ app.py
├─ data/
│  └─ sample_complaints.csv
├─ services/
│  ├─ __init__.py
│  └─ analyzer.py
├─ requirements.txt
└─ README.md
```

## 데이터 주의사항

- 모든 민원은 공모전 시연을 위한 가상 데이터입니다.
- 실제 국민신문고 데이터, 실제 민원 원문, 개인정보, 내부 시스템 정보는 사용하지 않습니다.
- 샘플 시설명은 `동탄권역 공공시설 A`, `서부권역 체육시설 B`, `이음터형 복합시설 C`, `공공도서관 D`처럼 비실명 가상명으로 작성했습니다.
- 실명, 전화번호, 상세 주소, 차량번호, 실제 민원번호, 직원명, 내부 부서명은 포함하지 않습니다.
- `.env`, `.streamlit/secrets.toml`, 가상환경 폴더, 캐시 파일은 `.gitignore`로 Git 업로드 대상에서 제외합니다.

## 분석 방식

첫 버전은 외부 AI API 없이 `services/analyzer.py`의 키워드 기반 규칙 분석으로 동작합니다.

- 분야: 주차, 안전, CCTV/개인정보, 시설이용, 프로그램, 대관, 환경, 행정안내
- 긴급도: 일반, 확인 필요, 주의, 즉시 확인 필요
- 담당 후보: 실제 부서명이 아닌 가상 담당 역할명
- 위험도 판단: 법적 판단이나 최종 판단이 아니라 담당자 우선 확인을 위한 참고 지표

## 향후 확장안

- 생성형 AI API 연동
- 민원 원문 비식별화
- 공공데이터 연계
- 부서별 반복 민원 분석

AI API 확장 위치는 `services/analyzer.py`의 `analyze_with_ai_api_placeholder()` 함수입니다. 향후 API를 붙이더라도 `app.py`는 `analyze_complaint()` 반환값만 사용하도록 구성되어 있어 화면 변경을 최소화할 수 있습니다.
