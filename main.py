"""
main.py
-------
효경언해(또는 다른 고문서) 이미지 한 장에 대해
전처리 -> OCR -> 후처리 -> (선택)평가 를 한 번에 실행하는 CLI.

사용 예 (backend 생략 시 기본값 tesseract 사용):
    python main.py data/raw/hyogyeong_6na.jpg \
        --vertical \
        --book "효경언해" \
        --page "6ㄴ" \
        --chapter "경(經) 1장 - (고문 제7장) 효평(孝平)" \
        --out data/output/hyogyeong_6na.json

PaddleOCR을 쓰고 싶다면 requirements.txt의 paddle 관련 줄 주석을 풀고
설치한 뒤 --backend paddle 을 명시적으로 붙이세요.

--ground-truth 옵션은 CER/WER 자동 계산 기능을 켭니다.
주의: 이 옵션에 세종한글고전 사이트의 교감 텍스트를 그대로 옮겨
사용하는 것은 저작권 위배 소지가 있습니다. README 3번 섹션을 반드시
먼저 읽어보세요.
"""

import argparse
import json
from pathlib import Path

from preprocess import preprocess
from ocr_engine import get_engine, results_to_text
from postprocess import postprocess, to_structured_record
from evaluate import cer, wer


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

    # 5. (선택) 평가 - 저작권 주의사항은 README 3번 참고
    if ground_truth_path and Path(ground_truth_path).exists():
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
    parser.add_argument("--ground-truth", default=None, help="CER/WER 평가용 정답 텍스트 경로 (README 3번 주의사항 참고)")
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
