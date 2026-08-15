# 효경언해 OCR 파이프라인

> 세종한글고전 사이트(`db.sejongkorea.org`)의 
>『효경언해』 6ㄴ면 등을 대상으로 만든 파이프라인입니다.

> Session 04 정리 내용(전처리 → 레이아웃 분석 → 문자 인식 → 후처리)을 그대로
> 코드로 구현한 기본 골격입니다.


## 0. 먼저 확인할 점: 원본 이미지 확보

이 사이트는 원본 이미지를 JS 뷰어(확대/축소/내려받기 버튼)로 서빙하고 있어서,
프로그램이 이미지 URL을 직접 크롤링할 수 있는 구조가 아니었습니다.
그래서 이 코드는 **로컬에 미리 저장한 이미지**를 입력으로 받습니다.

- 해당 페이지 접속 → "원본이미지" 탭에서 `효경언해 6ㄴ` 클릭
  http://db.sejongkorea.org/front/detail.do?bkCode=P08_HG_v001&recordId=P08_HG_e01_v001_0070
  → 뷰어의 내려받기(↓) 아이콘으로 저장, 또는 화면 캡처
- 저장한 파일을 `data/raw/hyogyeong_6na.jpg` 로 옮기기
- 혹은 원본 파일명 그대로 써도 됩니다. `P08_HG_e01_v001_006b.jpg`

## 1. 설치

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Tesseract 백엔드를 쓰려면 시스템에도 별도 설치가 필요합니다.

```bash
# Windows (PowerShell/CMD)
winget install --id UB-Mannheim.TesseractOCR -e
# ※ 기본 설치 경로는 'C:\Program Files\Tesseract-OCR'이며,
#    설치 후 이 경로를 시스템 환경 변수(PATH)에 직접 추가해야
#    명령 프롬프트에서 tesseract 명령이 인식됩니다.
# ※ 한국어(kor)·중국어 간체(chi_sim) 등 언어팩은 기본 설치에 포함되지
#    않는 경우가 많습니다. https://github.com/tesseract-ocr/tessdata 에서
#    kor.traineddata, chi_sim.traineddata 를 받아
#    'C:\Program Files\Tesseract-OCR\tessdata' 폴더에 넣어주세요.

# macOS
brew install tesseract tesseract-lang

# Ubuntu
sudo apt install tesseract-ocr tesseract-ocr-kor tesseract-ocr-chi-sim
```

## 2. 실행

```bash
python main.py data/raw/hyogyeong_6na.jpg \
    --vertical \
    --book "효경언해" \
    --page "6ㄴ" \
    --chapter "경(經) 1장 - (고문 제7장) 효평(孝平)" \
    --out data/output/hyogyeong_6na.json
```

- `--backend` 를 생략하면 기본값인 `tesseract`로 실행됩니다.
  PaddleOCR을 쓰려면 `requirements.txt`의 paddle 관련 줄 주석을 풀고
  설치한 뒤 `--backend paddle` 을 명시적으로 붙이세요.
- `--vertical` : 효경언해는 세로쓰기 목판본이므로 반드시 켜는 것을 권장.
  내부적으로 이미지를 90도 회전해 검출기에 넣고, 결과를 다시 원래 읽기
  순서로 정렬합니다. (`preprocess.py`, `ocr_engine.py` 참고)
- 단계별로 따로 실행하고 싶다면:
  ```bash
  python preprocess.py data/raw/hyogyeong_6na.jpg --vertical --out data/processed/6na.png
  python ocr_engine.py data/processed/6na.png --backend tesseract --vertical
  ```

## 3. 정확도 검증(CER/WER) - 기능은 있지만 실제로 실행해보지 않음

`evaluate.py`와 `main.py --ground-truth` 옵션으로 OCR 결과를 
정답 텍스트와 비교해 CER/WER을 계산하는 기능 자체는 구현해 뒀습니다.

**다만 이 저장소에서는 이 기능을 실제 세종한글고전 사이트의 텍스트로 실행해 검증한 적이 없습니다.** 

이유는 다음과 같습니다.

> 세종한글고전 사이트에 실린 언해문(예: 효경언해 6ㄴ면의 "언해" 탭 텍스트)은
> 세종대왕기념사업회가 교감·역주한 저작물입니다. 
> 이 텍스트를 그대로 `data/ground_truth/*.txt` 에 옮겨 담아 정답(reference)으로 사용하는 것은
> 그 저작물을 복제하여 코드 저장소나 실행 결과물에 포함시키는 셈이 되므로
> 저작권에 위배될 소지가 있습니다.

그래서 `--ground-truth` 옵션은 남겨뒀지만, 
이 저장소 자체에는 어떤 교감 텍스트도 담겨 있지 않고, 
`data/ground_truth/` 는 빈 폴더(`.gitkeep`)상태로만 유지됩니다. 

이 옵션을 실제로 쓰려면:

- 직접 저작권을 보유한 판독본/전사 데이터를 사용하거나
- 저작권자(세종대왕기념사업회)로부터 별도 이용 허락을 받은 뒤
- 개인 로컬 환경에서만 `data/ground_truth/`에 파일을 만들어 검증

```bash
python evaluate.py data/ground_truth/hyogyeong_6na.txt data/output/ocr_text.txt
# 또는
python main.py data/raw/hyogyeong_6na.jpg --vertical --ground-truth data/ground_truth/hyogyeong_6na.txt
```

`data/ground_truth/` 안의 실제 파일은 `.gitignore`로 커밋 대상에서 제외되어 있으니, 
로컬에서 검증용으로 채워 넣어도 git에는 올라가지 않습니다.

## 4. 다음 단계 (파인튜닝)

정리 내용에서 언급한 대로, 범용 PaddleOCR/Tesseract만으로는
필사체·이체자·고어 혼합 문헌의 정확도에 한계가 있습니다. 다음 단계로:

1. `data/raw/`에 여러 면 이미지를 모으고, 정답 텍스트는 저작권 문제가
   없는 경로(위 3번 참고)로 확보해 `data/ground_truth/`에 로컬로만 정리
2. HuggingFace `TrOCR`을 이 데이터로 파인튜닝 (`transformers` 이미 requirements에 포함)
3. `postprocess.py`의 `VARIANT_CHAR_MAP`을 실제 이체자 사례로 계속 확장
4. `to_structured_record()`에 인명·연호·서명 개체명 태깅 로직 추가

## 폴더 구조

```
ocr_hyogyeong/
├── .gitignore           # data/ 하위 실제 파일 커밋 방지
├── requirements.txt
├── preprocess.py         # 1단계: 이진화/노이즈제거/기울기보정
├── ocr_engine.py         # 2~3단계: 레이아웃 분석 + 문자 인식 (PaddleOCR/Tesseract)
├── postprocess.py        # 4단계: 이체자 정규화 + 구조화
├── evaluate.py           # CER/WER 평가 (실사용 시 저작권 주의 - 3번 참고)
├── main.py               # 전체 파이프라인 CLI
├── data/
│   ├── raw/              # 원본 이미지 (직접 다운로드해서 넣기)
│   ├── processed/        # 전처리 결과
│   ├── output/           # OCR 결과 JSON
│   └── ground_truth/     # (선택) 정답 텍스트 - 배포 금지, 로컬 전용 (배포를 원하시거든 원 저작자와 상의하시길 바랍니다.)
└── README.md
```