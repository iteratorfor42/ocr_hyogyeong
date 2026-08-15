"""
ocr_engine.py
-------------
정리 내용의 2~3단계(레이아웃 분석 + 문자 인식) 담당.

두 가지 백엔드를 제공:
  1) PaddleOCR  : 검출(det) + 인식(rec)이 통합되어 있어 커스텀 데이터로
                  파인튜닝하기 수월함 (정리 내용 참고 도구 그대로 채택)
  2) Tesseract  : 범용 OCR 비교군. 활자본에는 강하지만 필사체엔 한계가
                  뚜렷하므로 baseline 비교용으로만 사용 권장.

한자+옛한글(이두/고어)이 섞인 문서라 두 백엔드 모두 완전하지 않음.
실제 정확도를 올리려면 결국 TrOCR류를 한국 고문서 데이터로
파인튜닝하는 방향이 필요 (README 참고).
"""

from dataclasses import dataclass
from typing import Literal
import numpy as np


@dataclass
class OCRResult:
    text: str
    confidence: float
    box: list  # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]


class PaddleOCRBackend:
    def __init__(self, lang: str = "korean", use_gpu: bool = False):
        from paddleocr import PaddleOCR  # 지연 import (설치 안 됐을 때 다른 백엔드는 쓸 수 있게)

        # 한자가 섞인 경우 lang="ch" 가 한자 인식률이 더 나을 수 있어
        # 실제 데이터로 두 설정을 비교해보는 것을 권장.
        self.engine = PaddleOCR(use_angle_cls=True, lang=lang, use_gpu=use_gpu, show_log=False)

    def run(self, img: np.ndarray) -> list[OCRResult]:
        raw = self.engine.ocr(img, cls=True)
        results = []
        if not raw or raw[0] is None:
            return results
        for line in raw[0]:
            box, (text, conf) = line
            results.append(OCRResult(text=text, confidence=conf, box=box))
        return results


class TesseractBackend:
    def __init__(self, lang: str = "kor+chi_sim"):
        # 시스템에 tesseract-ocr-kor, tesseract-ocr-chi-sim(또는 chi_tra) 설치 필요
        self.lang = lang

    def run(self, img: np.ndarray) -> list[OCRResult]:
        import pytesseract
        from pytesseract import Output

        data = pytesseract.image_to_data(img, lang=self.lang, output_type=Output.DICT)
        results = []
        n = len(data["text"])
        for i in range(n):
            text = data["text"][i].strip()
            if not text:
                continue
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            conf = float(data["conf"][i]) / 100 if data["conf"][i] != "-1" else 0.0
            box = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
            results.append(OCRResult(text=text, confidence=conf, box=box))
        return results


def get_engine(backend: Literal["paddle", "tesseract"] = "paddle", **kwargs):
    if backend == "paddle":
        return PaddleOCRBackend(**kwargs)
    elif backend == "tesseract":
        return TesseractBackend(**kwargs)
    raise ValueError(f"지원하지 않는 backend: {backend}")


def results_to_text(results: list[OCRResult], vertical: bool = False) -> str:
    """
    검출된 라인들을 읽기 순서대로 정렬해 하나의 문자열로 합침.
    vertical=True면 원본이 세로쓰기였고(preprocess에서 90도 회전 후 인식했다는 가정),
    실제 원문 순서(우->좌 열)로 복원하기 위해 box의 x좌표 기준 내림차순으로 정렬.
    """
    if not results:
        return ""

    if vertical:
        # 회전된 이미지 기준 y좌표(=원본의 열 순서)로 정렬 후,
        # 같은 열 안에서는 x좌표(=원본의 세로 방향 위->아래)로 정렬
        sorted_results = sorted(
            results, key=lambda r: (r.box[0][1], r.box[0][0])
        )
    else:
        sorted_results = sorted(
            results, key=lambda r: (r.box[0][1], r.box[0][0])
        )

    return "\n".join(r.text for r in sorted_results)


if __name__ == "__main__":
    import argparse
    import cv2

    parser = argparse.ArgumentParser(description="전처리된 이미지에 OCR 실행")
    parser.add_argument("image_path")
    parser.add_argument("--backend", choices=["paddle", "tesseract"], default="paddle")
    parser.add_argument("--vertical", action="store_true")
    args = parser.parse_args()

    img = cv2.imread(args.image_path)
    engine = get_engine(args.backend)
    results = engine.run(img)
    text = results_to_text(results, vertical=args.vertical)
    print(text)
