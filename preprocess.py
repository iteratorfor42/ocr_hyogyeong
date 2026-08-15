"""
preprocess.py
-------------
고문서/필사본 이미지 전처리 모듈.

정리 내용의 1단계(전처리) 담당:
- 이진화 (Otsu)
- 노이즈 제거
- 기울기 보정 (deskew)
- 세로쓰기 문서 대응: 필요 시 90도 회전 옵션 제공
  (PaddleOCR/CRAFT류 검출기는 기본적으로 가로쓰기에 최적화되어 있어서,
   세로쓰기 원문은 90도 회전 후 검출하면 인식률이 크게 개선되는 경우가 많음)
"""

import cv2
import numpy as np
from pathlib import Path


def load_image(image_path: str) -> np.ndarray:
    img = cv2.imread(str(image_path))
    if img is None:
        raise FileNotFoundError(
            f"이미지를 열 수 없습니다: {image_path}\n"
            f"세종한글고전 사이트는 이미지를 JS 뷰어로 서빙하므로, "
            f"'내려받기' 버튼이나 캡처를 이용해 로컬에 먼저 저장해야 합니다."
        )
    return img


def to_grayscale(img: np.ndarray) -> np.ndarray:
    if len(img.shape) == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img


def binarize(gray: np.ndarray) -> np.ndarray:
    """Otsu 이진화. 얼룩/훼손이 심한 경우 adaptive threshold로 교체 고려."""
    _, binarized = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return binarized


def denoise(binarized: np.ndarray, h: int = 15) -> np.ndarray:
    return cv2.fastNlMeansDenoising(binarized, h=h)


def deskew(img: np.ndarray) -> np.ndarray:
    """
    간단한 기울기 보정. 텍스트 영역의 최소 외접 사각형 각도를 이용.
    고문서는 스캔 각도가 미세하게 틀어진 경우가 많아 이 단계가 인식률에 영향을 준다.
    """
    coords = np.column_stack(np.where(img > 0))
    if len(coords) == 0:
        return img
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )
    return rotated


def rotate_for_vertical_text(img: np.ndarray, clockwise: bool = True) -> np.ndarray:
    """
    세로쓰기(우->좌, 위->아래) 원문을 가로쓰기 검출기에 맞게 90도 회전.
    효경언해처럼 한 면에 여러 세로줄이 있는 목판/필사본에 유용.
    """
    code = cv2.ROTATE_90_CLOCKWISE if clockwise else cv2.ROTATE_90_COUNTERCLOCKWISE
    return cv2.rotate(img, code)


def preprocess(
    image_path: str,
    vertical: bool = False,
    save_path: str | None = None,
) -> np.ndarray:
    """전체 전처리 파이프라인. 최종 이진화+노이즈 제거+기울기 보정 이미지를 반환."""
    img = load_image(image_path)
    gray = to_grayscale(img)
    binarized = binarize(gray)
    denoised = denoise(binarized)
    deskewed = deskew(denoised)

    if vertical:
        deskewed = rotate_for_vertical_text(deskewed)

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(save_path), deskewed)

    return deskewed


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="고문서 이미지 전처리")
    parser.add_argument("image_path", help="원본 이미지 경로 (예: data/raw/hyogyeong_24na.jpg)")
    parser.add_argument("--out", default="data/processed/preprocessed.png")
    parser.add_argument("--vertical", action="store_true", help="세로쓰기 문서면 90도 회전")
    args = parser.parse_args()

    preprocess(args.image_path, vertical=args.vertical, save_path=args.out)
    print(f"전처리 완료 -> {args.out}")
