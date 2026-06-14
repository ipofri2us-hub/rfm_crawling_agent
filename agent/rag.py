"""
과거 실패 이력(data/failure_cases/*.md)을 LanceDB에 벡터로 저장해두고,
신규 항목이 과거 실패 사례와 유사하면 "실물 평가 기각"으로 게이팅합니다.

임베딩은 외부 모델/API 없이 동작하도록 간단한 hashing-trick
bag-of-words 방식을 사용합니다 (필요하면 나중에 실제 임베딩 모델로 교체 가능).
"""

import glob
import hashlib
import os
import re

import lancedb

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "lancedb")
FAILURE_CASES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "failure_cases"
)

FAILURE_TABLE = "failure_cases"
EMBED_DIM = 128

# LanceDB의 L2 distance가 이 값보다 작으면(=유사하면) 과거 실패 사례와
# 유사하다고 판단하고 게이팅합니다. (정규화된 벡터 기준, 값이 작을수록 엄격)
SIMILARITY_DISTANCE_THRESHOLD = 1.2


def _embed(text: str) -> list[float]:
    """아주 단순한 hashing-trick bag-of-words 임베딩."""
    vec = [0.0] * EMBED_DIM
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        idx = int(hashlib.md5(word.encode()).hexdigest(), 16) % EMBED_DIM
        vec[idx] += 1.0

    norm = sum(v * v for v in vec) ** 0.5
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def _get_table():
    os.makedirs(DB_DIR, exist_ok=True)
    db = lancedb.connect(DB_DIR)

    if FAILURE_TABLE in db.table_names():
        return db.open_table(FAILURE_TABLE)

    rows = []
    for path in sorted(glob.glob(os.path.join(FAILURE_CASES_DIR, "*.md"))):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        rows.append({"id": os.path.basename(path), "text": text, "vector": _embed(text)})

    if not rows:
        return None

    return db.create_table(FAILURE_TABLE, data=rows)


def check_failure_history(item: dict) -> dict:
    """과거 실패 이력과 유사한 항목인지 검사합니다.

    반환: {"rejected": bool, "matched_doc": str | None, "reason": str}
    """
    try:
        table = _get_table()
        if table is None:
            return {"rejected": False, "matched_doc": None, "reason": "등록된 실패 이력이 없음"}

        query_vec = _embed(f"{item['title']} {item['summary']}")
        results = table.search(query_vec).limit(1).to_list()
        if not results:
            return {"rejected": False, "matched_doc": None, "reason": "등록된 실패 이력이 없음"}

        match = results[0]
        distance = match["_distance"]
        doc_id = match["id"]
        doc_text = match["text"]

        if distance <= SIMILARITY_DISTANCE_THRESHOLD:
            return {
                "rejected": True,
                "matched_doc": doc_id,
                "reason": (
                    f"과거 실패 이력 '{doc_id}'와 유사 (distance={distance:.2f}) -> 실물 평가 기각\n"
                    f"근거 문서 일부: {doc_text[:200]}..."
                ),
            }

        return {
            "rejected": False,
            "matched_doc": None,
            "reason": f"가장 유사한 실패 이력 '{doc_id}' distance={distance:.2f} (임계치 미달, 통과)",
        }

    except Exception as e:
        return {
            "rejected": False,
            "matched_doc": None,
            "reason": f"RAG 게이팅 실행 중 오류로 건너뜀: {e}",
        }
