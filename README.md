# 별채우기 — 한국사 암기

아이패드와 아이폰 Safari에서 사용할 수 있는 반응형 한국사 빈칸 암기 웹앱입니다. 단원 학습, 초성 힌트, 정답 확인, 기억 확신도 표시, 오답 복습과 기기별 로컬 진도 저장을 제공합니다.

## 디렉토리 구조

```text
start_history/
├── index.html                 # 앱 진입점
├── manifest.webmanifest       # 홈 화면 설치 설정
├── sw.js                      # 오프라인 캐시
├── assets/
│   ├── main.js                # 학습·복습 동작
│   ├── styles.css             # 반응형 화면 스타일
│   └── star.svg               # 앱 아이콘
├── data/
│   └── questions.json         # 전체 범위 문항 데이터
├── scripts/
│   └── extract_questions.py   # 제공 PDF에서 JSON 추출
└── README.md
```

## 로컬에서 실행

서비스 워커와 홈 화면 설치 기능을 사용하려면 HTTPS 또는 localhost에서 제공해야 합니다.

```sh
python3 -m http.server 8000
```

브라우저에서 `http://localhost:8000`을 여세요. 같은 네트워크의 iPad Safari에서 확인할 때는 개발 컴퓨터의 로컬 IP 주소로 접속하면 됩니다.

## 문항 데이터

`data/questions.json`에는 제공된 PDF에서 추출한 39강, 1,057개 문항이 들어 있습니다. 추출 과정의 원문 페이지와 경고 정보도 각 데이터에 기록되어 있습니다. PDF 원본은 저장소에 포함하지 않습니다.

다시 추출하려면 `pdfplumber`가 설치된 Python 환경에서 실행합니다.

```sh
python3 -m pip install pdfplumber
python3 scripts/extract_questions.py "/path/to/최태성 한능검 심화 별채우기_전범위.pdf" --output data/questions.json
```

## 공개 배포

현재 GitHub 저장소는 비공개이며 Pages 배포 워크플로는 포함하지 않았습니다. Pages를 활성화하면 정적 앱의 문항 데이터도 인터넷에서 접근할 수 있으므로, 권리자 허락을 확인한 뒤 공개 배포 설정을 추가해야 합니다.

## 전체 문항 검수

자동 구조 점검:

```sh
python3 scripts/audit_questions.py
```

PDF와 대조하려면 로컬 서버를 실행하고 `http://localhost:8766/review.html`을 여세요. `PDF 선택`에서 원본을 고르면 현재 문항의 PDF 쪽으로 이동합니다. PDF는 브라우저 안에서만 열리며 서버나 GitHub로 전송되지 않습니다. 검수 상태는 현재 브라우저의 로컬 저장소에 저장되고, 검수 기록은 JSON으로 내보내거나 다시 불러올 수 있습니다.

```sh
python3 -m http.server 8766
```

자동 점검은 구조 오류를 찾는 보조 수단이며 역사적 정확성을 판단하지 않습니다. 문장·빈칸·정답은 PDF 원문과 직접 대조해야 합니다.
