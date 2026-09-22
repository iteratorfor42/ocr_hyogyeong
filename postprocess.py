"""
postprocess.py
---------------
정리 내용의 4단계(후처리) 담당: 이체자/이형자 정규화 + 구조화된 데이터 변환.

"OCR 정확도 못지않게, 인식된 텍스트를 구조화된 데이터
(예: 인명·지명·연호 태깅)로 전환할지가 인문학적 활용의 관건이라 접근"

여기서는 최소 골격만 제공. 
실제 프로젝트에서는
- 이체자 매핑 테이블을 사전(dict)이나 별도 CSV로 계속 확장하고
- 인명/연호/서명 등 개체명 태깅 로직을 추가해야 함.
 (일단 필자는 관련 용어 사전 예시를 작성할 수 없었고,
  이런 사전은 관련 전공자가 해야 한다고 생각하여 최소 골격만 마련.)
"""

import re
import unicodedata

# 이체자/이형자 정규화 예시 테이블 (실제 데이터로 계속 채워나가야 함)
# key: 원문에서 인식된 형태, value: 정규화된 형태
VARIANT_CHAR_MAP: dict[str, str] = {
    # 예시: "藥": "藥",  # 이체자 -> 정자
    # 실제 효경언해류 문헌에서 자주 나오는 이체자를 조사해 채워 넣을 것
}

# 옛한글 자모 중 OCR이 혼동하기 쉬운 문자 쌍 (필요시 확장)
COMMON_OCR_CONFUSIONS: dict[str, str] = {
    # "ㆍ": "·",  # 아래아 <-> 가운뎃점 혼동 예시
}


def normalize_unicode(text: str) -> str:
    """유니코드 정규화 (NFC). 옛한글 자모 조합 형태 통일에 필수."""
    return unicodedata.normalize("NFC", text)


def apply_variant_map(text: str, mapping: dict[str, str] = VARIANT_CHAR_MAP) -> str:
    for src, dst in mapping.items():
        text = text.replace(src, dst)
    return text


def clean_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def postprocess(raw_text: str) -> str:
    text = normalize_unicode(raw_text)
    text = apply_variant_map(text)
    text = clean_whitespace(text)
    return text


def to_structured_record(
    text: str,
    book: str = "효경언해",
    page: str = "",
    chapter: str = "",
) -> dict:
    """
    단순 텍스트를 인문학적 활용이 가능한 구조화된 레코드로 변환.
    실제로는 여기에 인명(person), 연호(era_name), 서명(book_title) 등의
    개체명 태깅 결과를 추가해 나가면 됨.
    """
    return {
        "book": book,
        "page": page,
        "chapter": chapter,
        "text": text,
        "entities": {
            "person": [],
            "place": [],
            "era_name": [],
        },
    }


if __name__ == "__main__":
    # 예시: 효경언해 6ㄴ면, (고문 제7장) 효평(孝平) 원문 중 일부
    sample = "孝효無무終죵始시오 而이患환不블及급者쟈"
    print(postprocess(sample))