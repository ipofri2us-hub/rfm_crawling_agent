"""
RFM Crawling Agent 진입점.

실행: python main.py

흐름: 수집 -> 도메인 필터(AI) -> 신뢰도/하드웨어 판단 -> RAG 게이팅
      -> 초록 요약(AI) -> DB 저장 -> 리포트 생성
"""

import sys

import yaml

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from agent import collectors, db, filters, rag, report, summarizer


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    config = load_config()
    db.init_db()

    print("[1/5] 수집 중...")
    items = collectors.collect_all(config)
    print(f"  -> {len(items)}건 수집")

    accepted, rejected, dropped = [], [], []

    for item in items:
        print(f"[2/5] 도메인 판단: {item['title'][:60]}")
        item["domain"] = filters.domain_filter(item)
        if not item["domain"]["is_relevant"]:
            db.save_item(item, status="dropped")
            dropped.append(item)
            continue

        item["credibility"] = filters.credibility_score(item, config)
        item["hw_compat"] = filters.hw_compat_check(item, config)

        print("[3/5] RAG 게이팅...")
        item["rag_gate"] = rag.check_failure_history(item)
        if item["rag_gate"]["rejected"]:
            db.save_item(item, status="rejected")
            rejected.append(item)
            continue

        print("[4/5] 초록 요약...")
        item["ai_summary"] = summarizer.summarize_item(item)
        db.save_item(item, status="accepted")
        accepted.append(item)

    print(
        f"  -> 통과 {len(accepted)}건 / RAG 기각 {len(rejected)}건 / "
        f"도메인 제외 {len(dropped)}건"
    )

    print("[5/5] 리포트 생성...")
    all_items = db.get_all_items()
    report_text = report.generate_and_save(all_items)
    report.send_to_slack(report_text)


if __name__ == "__main__":
    main()
