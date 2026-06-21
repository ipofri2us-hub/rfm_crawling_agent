"""
RAG 게이팅을 통과한 항목의 원문 초록(summary)을 한국어로 간단히 요약합니다.

신뢰도/하드웨어/RAG 판단 근거는 영문 원문 그대로 남아 있어 사람이 빠르게 읽기
어려우므로, 사람이 리포트만 보고도 "이게 뭔지" 판단할 수 있도록 돕는 보조 정보입니다.
"""

import json

from agent.llm import ask_llm


def summarize_item(item: dict) -> dict:
    """LLM에게 원문 초록을 한국어로 요약하도록 요청합니다.

    반환: {"summary_ko": str}
    """
    prompt = (
        "TASK: summarize\n"
        f"TITLE: {item['title']}\n"
        f"SUMMARY: {item['summary']}\n"
        "위 논문/레포의 초록을 한국어 3문장 이내로 요약하세요. 어떤 방법을 쓰는지, "
        "어떤 결과/주장을 하는지가 드러나야 합니다. "
        'JSON으로만 답하세요: {"summary_ko": "..."}'
    )

    try:
        response = ask_llm(prompt)
        result = json.loads(response)
    except Exception:
        result = {"summary_ko": f"LLM 요약 실패로 원문을 그대로 표시합니다: {item['summary']}"}

    return result
