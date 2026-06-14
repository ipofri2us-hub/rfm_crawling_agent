"""
수집/판단 결과를 LanceDB에 저장하고 조회하는 모듈.

각 항목은 JSON 형태 그대로 'data' 컬럼에 저장하고, 검색/정렬에 자주 쓰는
url/title/source/status만 별도 컬럼으로 둡니다. (벡터 검색이 필요한
실패 이력 RAG는 rag.py에서 같은 LanceDB 디렉터리의 다른 테이블을 사용합니다.)
"""

import json
import os

import lancedb

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "lancedb")

ITEMS_TABLE = "items"


def init_db():
    os.makedirs(DB_DIR, exist_ok=True)


def save_item(item: dict, status: str):
    """item을 저장합니다. 같은 url이 이미 있으면 덮어씁니다 (upsert).

    status: "dropped" | "rejected" | "accepted"
    """
    row = {
        "url": item["url"],
        "title": item["title"],
        "source": item["source"],
        "status": status,
        "data": json.dumps(item, ensure_ascii=False),
    }

    db = lancedb.connect(DB_DIR)

    if ITEMS_TABLE not in db.table_names():
        db.create_table(ITEMS_TABLE, data=[row])
        return

    table = db.open_table(ITEMS_TABLE)
    (
        table.merge_insert("url")
        .when_matched_update_all()
        .when_not_matched_insert_all()
        .execute([row])
    )


def get_all_items() -> list[dict]:
    """저장된 모든 항목을 최신 실행 결과 그대로 반환합니다."""
    db = lancedb.connect(DB_DIR)
    if ITEMS_TABLE not in db.table_names():
        return []

    table = db.open_table(ITEMS_TABLE)

    items = []
    for row in table.to_pandas().to_dict("records"):
        item = json.loads(row["data"])
        item["status"] = row["status"]
        items.append(item)
    return items
