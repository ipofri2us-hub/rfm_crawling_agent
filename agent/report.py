"""
파이프라인 결과를 Markdown 리포트로 만들어 저장하고, 설정되어 있으면
Slack으로도 전송합니다.
"""

import os
from datetime import datetime

import requests

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "reports")


def generate_and_save(items: list[dict]) -> str:
    """items를 status별로 정리한 Markdown 리포트를 생성하고 파일로 저장합니다."""
    accepted = [i for i in items if i["status"] == "accepted"]
    rejected = [i for i in items if i["status"] == "rejected"]
    dropped = [i for i in items if i["status"] == "dropped"]

    run_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"# RFM 주간 리포트 ({run_at})", ""]
    lines.append(f"- 수집: {len(items)}건 / 통과: {len(accepted)}건 / "
                  f"RAG 기각: {len(rejected)}건 / 도메인 제외: {len(dropped)}건")
    lines.append("")

    lines.append("## 1. 통과 항목 (실물 평가 후보)")
    if not accepted:
        lines.append("- 없음")
    for item in accepted:
        lines.append(f"### {item['title']}")
        lines.append(f"- 출처: {item['source']} | URL: {item['url']}")
        lines.append(f"- 도메인 판단: {item['domain']['reason']} (score={item['domain']['score']})")
        lines.append(f"- 신뢰도: {item['credibility']['reason']}")
        lines.append(f"- 하드웨어 호환성: {item['hw_compat']['reason']}")
        lines.append("")
        lines.append(f"> **AI 요약**: {item['ai_summary'].get('summary_ko', '요약 없음')}")
        lines.append("")

    lines.append("## 2. RAG 기각 항목 (과거 실패 이력과 유사 -> 실물 평가 보류)")
    if not rejected:
        lines.append("- 없음")
    for item in rejected:
        lines.append(f"- **{item['title']}** ({item['url']})")
        lines.append(f"  - {item['rag_gate']['reason']}")

    lines.append("")
    lines.append("## 3. 도메인 제외 항목")
    if not dropped:
        lines.append("- 없음")
    for item in dropped:
        lines.append(f"- {item['title']} - {item['domain']['reason']}")

    report_text = "\n".join(lines)
    _save(report_text)
    return report_text


def _save(report_text: str):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    path = os.path.join(REPORTS_DIR, f"{timestamp}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"[report] 저장 완료: {path}")


def send_to_slack(report_text: str):
    """SLACK_WEBHOOK_URL이 설정된 경우에만 Slack으로 전송합니다."""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("[report] SLACK_WEBHOOK_URL이 설정되지 않아 Slack 전송을 건너뜁니다.")
        return

    try:
        requests.post(webhook_url, json={"text": report_text}, timeout=10)
        print("[report] Slack 전송 완료")
    except requests.RequestException as e:
        print(f"[report] Slack 전송 실패: {e}")
