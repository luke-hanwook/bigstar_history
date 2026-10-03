# 별채우기 — 아이패드 웹앱

아이패드 Safari에서 사용할 수 있는 반응형 한국사 빈칸 암기 웹앱입니다. 단원 선택, 문장형 빈칸 입력, 힌트, 정답 확인, 기억 확신도 표시, 오답/헷갈림 복습과 로컬 진도 저장을 제공합니다.

## 실행

정적 파일로 동작합니다. 서비스 워커와 홈 화면 설치 기능을 쓰려면 HTTPS 또는 localhost에서 제공해야 합니다.

```sh
python3 -m http.server 8000
```

브라우저에서 `http://localhost:8000`을 여세요. 같은 네트워크의 iPad Safari에서 쓰려면 개발 컴퓨터의 로컬 IP 주소로 접속하면 됩니다. 홈 화면 추가 메뉴를 사용하면 standalone 모드로 실행할 수 있습니다.

## GitHub Pages 배포

`.github/workflows/pages.yml`은 `main` 브랜치에 반영될 때 GitHub Pages로 앱을 배포합니다. 저장소 설정의 **Pages → Build and deployment → Source**에서 **GitHub Actions**를 선택해야 합니다. 게시되는 파일은 앱 실행에 필요한 정적 파일과 `questions.json`입니다.

GitHub Pages로 게시한 사이트와 문항 데이터는 인터넷에 공개됩니다. 문항 사용·배포 권한을 확인한 뒤 저장소에 올리세요. `*.pdf`는 실수로 원본 PDF가 저장소에 추가되지 않도록 제외했습니다.

## 전체 범위 문항 데이터

`questions.json`에는 제공된 PDF에서 추출한 39강, 1,057개 문항이 강·문항·정답으로 정리되어 있습니다. PDF 텍스트 추출 특성상 원본의 오탈자와 몇몇 정답 번호 중복이 그대로 반영될 수 있으며, 각 문항에는 원문 대조를 돕는 페이지와 추출 경고가 기록됩니다.

PDF를 다시 추출하려면 `pdfplumber`가 설치된 Python 환경에서 실행합니다.

```sh
python3 -m pip install pdfplumber
python3 extract_questions.py "/path/to/최태성 한능검 심화 별채우기_전범위.pdf"
```

앱은 시작할 때 `questions.json`을 불러오며, 서비스 워커가 이 파일도 캐시합니다. 이 데이터 파일은 제공된 학습 자료에서 추출한 것이므로 배포·공개 전 콘텐츠 사용 권한을 확인하세요.

## 파일

- `index.html`: 화면 구조
- `styles.css`: 반응형 스타일 및 iPad 레이아웃
- `main.js`: 학습/복습 흐름과 로컬 저장
- `questions.json`: 전체 범위 문항·정답 데이터
- `extract_questions.py`: 제공 PDF에서 JSON을 다시 생성
- `manifest.webmanifest`, `sw.js`: PWA 설치 정보와 오프라인 앱 셸
