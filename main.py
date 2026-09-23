"""
main.py
-------
효경언해(또는 다른 고문서) 이미지 한 장에 대해
전처리 -> OCR -> 후처리 -> (선택)평가를 한 번에 실행하는 CLI.

사용 예 (backend 생략 시 기본값 tesseract 사용):
    python main.py data/raw/hyogyeong_6na.jpg \
        --vertical \
        --book "효경언해" \
        --page "6ㄴ" \
        --chapter "경(經) 1장 - (고문 제7장) 효평(孝平)" \
        --out data/output/hyogyeong_6na.json

PaddleOCR을 쓰고 싶다면 requirements.txt의 paddle 관련 줄 주석을 풀고 설치한 뒤 
--backend paddle 을 명시적으로 붙이세요.
(일단 ocr_engine에서는 PaddleOCR을 글로벌이 아닌 init에 넣었습니다.)

--ground-truth 옵션(CER/WER 자동 계산)은 기본적으로 꺼져 있습니다.
켜려면 아래 ENABLE_GROUND_TRUTH_EVAL 값을 코드에서 직접 True로 바꿔야 합니다. 
--ground-truth 플래그만 붙인다고 켜지지 않도록 일부러 막아둔 것이니, 
필요한 사람만 의도적으로 코드를 수정해서 사용하세요.
(일단 이 작업 경우 KPoEM 작업보다는 저작권을 더 많이 고려했습니다.
*주의* 다른 글에서도 언급했듯, 
세종한글고전 사이트의 교감 텍스트를 그대로 옮겨 정답으로 쓰는 것은 저작권 위배 소지가 있습니다. 
코드 안전장치는 거의 다 마련해 놨지만, 
AI 통해 바이브코딩을 할 경우 안전장치가 다 사라져 버릴 수 있으니 README 3번 섹션을 반드시 먼저 읽어보세요. 

"""

import argparse
import json
from pathlib import Path

from preprocess import preprocess
from ocr_engine import get_engine, results_to_text
from postprocess import postprocess, to_structured_record
from evaluate import cer, wer

# 정확도 검증(CER/WER) 기능의 온/오프 스위치.
# 상단에 언급한 것처럼 --ground-truth 플래그만으로는 켜지지 않고, 
# 이 값을 True로 바꿔야만 실제로 평가가 수행됩니다. (README 3번: 저작권 주의사항 먼저 확인)
ENABLE_GROUND_TRUTH_EVAL = False


def run_pipeline(
    image_path: str,
    vertical: bool,
    backend: str,
    book: str,
    page: str,
    chapter: str,
    ground_truth_path: str | None,
    out_path: str,
):
    # 1. 전처리
    processed_img = preprocess(image_path, vertical=vertical)

    # 2~3. 레이아웃 분석 + 문자 인식
    engine = get_engine(backend)
    raw_results = engine.run(processed_img)
    raw_text = results_to_text(raw_results, vertical=vertical)

    # 4. 후처리
    final_text = postprocess(raw_text)
    record = to_structured_record(final_text, book=book, page=page, chapter=chapter)

    # 5. (선택) 평가 - 기본적으로 비활성화. 저작권 주의사항은 README 3번 참고
    if ground_truth_path:
        if not ENABLE_GROUND_TRUTH_EVAL:
            print(
                "[안내] 정확도 검증(CER/WER) 기능은 기본적으로 꺼져 있습니다.\n"
                "       사용하려면 main.py 상단의 ENABLE_GROUND_TRUTH_EVAL 값을\n"
                "       True로 직접 바꾼 뒤 다시 실행하세요. (README 3번 참고)"
            )
        elif Path(ground_truth_path).exists():
            with open(ground_truth_path, encoding="utf-8") as f:
                reference = f.read()
            record["evaluation"] = {
                "CER": round(cer(reference, final_text), 4),
                "WER": round(wer(reference, final_text), 4),
            }

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    print(json.dumps(record, ensure_ascii=False, indent=2))
    print(f"\n결과 저장 완료 -> {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="고문서 OCR 파이프라인 (효경언해 예시)")
    parser.add_argument("image_path", help="원본 이미지 경로")
    parser.add_argument("--vertical", action="store_true", help="세로쓰기 문서 여부")
    parser.add_argument("--backend", choices=["paddle", "tesseract"], default="tesseract")
    parser.add_argument("--book", default="효경언해")
    parser.add_argument("--page", default="")
    parser.add_argument("--chapter", default="")
    parser.add_argument(
        "--ground-truth",
        default=None,
        help=(
            "CER/WER 평가용 정답 텍스트 경로."
            "이 플래그만으로는 평가가 켜지지  않고, main.py의 ENABLE_GROUND_TRUTH_EVAL을 True로 바꿔야 동작함. "
            "(README 3번 주의사항 참고)"
        ),
    )
    parser.add_argument("--out", default="data/output/result.json")
    args = parser.parse_args()

    run_pipeline(
        image_path=args.image_path,
        vertical=args.vertical,
        backend=args.backend,
        book=args.book,
        page=args.page,
        chapter=args.chapter,
        ground_truth_path=args.ground_truth,
        out_path=args.out,
    )