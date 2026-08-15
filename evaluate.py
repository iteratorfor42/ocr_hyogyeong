"""
evaluate.py
-----------
OCR 결과를 정답(ground truth) 텍스트와 비교해 CER/WER을 계산.

주의: 이 저장소는 이 기능을 세종한글고전 사이트의 교감 텍스트로
실제 실행해 검증한 적이 없습니다. 
자세한 이유는 README 3번 섹션을 참고하세요
(요약 : 교감 텍스트를 입력으로 사용하는 것 자체가 저작권 위배 소지가 있음).
"""

import Levenshtein as lev


def cer(reference: str, hypothesis: str) -> float:
    """문자 단위 오류율 (Character Error Rate)."""
    reference = reference.replace(" ", "").replace("\n", "")
    hypothesis = hypothesis.replace(" ", "").replace("\n", "")
    if len(reference) == 0:
        return 0.0 if len(hypothesis) == 0 else 1.0
    distance = lev.distance(reference, hypothesis)
    return distance / len(reference)


def wer(reference: str, hypothesis: str) -> float:
    """어절(공백 기준) 단위 오류율 (Word Error Rate)."""
    ref_words = reference.split()
    hyp_words = hypothesis.split()
    if len(ref_words) == 0:
        return 0.0 if len(hyp_words) == 0 else 1.0
    distance = lev.distance(ref_words, hyp_words)
    return distance / len(ref_words)


def evaluate(reference_path: str, hypothesis_path: str) -> dict:
    with open(reference_path, encoding="utf-8") as f:
        reference = f.read()
    with open(hypothesis_path, encoding="utf-8") as f:
        hypothesis = f.read()

    return {
        "CER": round(cer(reference, hypothesis), 4),
        "WER": round(wer(reference, hypothesis), 4),
    }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="OCR 결과 CER/WER 평가")
    parser.add_argument("reference_path", help="정답 텍스트 파일 경로")
    parser.add_argument("hypothesis_path", help="OCR 결과 텍스트 파일 경로")
    args = parser.parse_args()

    scores = evaluate(args.reference_path, args.hypothesis_path)
    print(json.dumps(scores, ensure_ascii=False, indent=2))
