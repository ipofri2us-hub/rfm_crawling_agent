"""
RAG 게이팅을 통과한 항목의 원문 초록(summary)을 한국어로 간단히 요약합니다.

신뢰도/하드웨어/RAG 판단 근거는 영문 원문 그대로 남아 있어 사람이 빠르게 읽기
어려우므로, 사람이 리포트만 보고도 "이게 뭔지" 판단할 수 있도록 돕는 보조 정보입니다.
"""

from agent.llm import ask_llm, parse_json_response


def summarize_item(item: dict) -> dict:
    """LLM에게 원문 초록을 한국어로 번역/요약하고, 그 의미/시사점을 설명하도록 요청합니다.

    반환: {"abstract_ko": str, "summary_ko": str, "meaning_ko": str}
    """
    prompt = (
        "TASK: summarize\n"
        f"TITLE: {item['title']}\n"
        f"SUMMARY: {item['summary']}\n"
        "위 논문/레포의 초록을 바탕으로 아래 세 가지를 한국어로 작성하세요.\n"
        "1. abstract_ko: 원문 초록(SUMMARY)을 빠뜨리는 내용 없이 한국어로 전체 번역.\n"
        "2. summary_ko: 2문장 이내로 핵심 요약. 어떤 방법을 쓰는지, 어떤 결과/주장을 하는지가 드러나야 합니다.\n"
        "3. meaning_ko: 1~2문장으로 이 연구가 우리 RFM/로봇 매니퓰레이션 작업에 어떤 의미가 있는지, "
        "왜 주목할 만한지를 설명하세요.\n"
        "다른 설명 없이 JSON 한 줄만 출력하고, 각 값 안에서는 줄바꿈이나 마크다운(글머리표, 굵게 등)을 "
        "쓰지 마세요: "
        '{"abstract_ko": "...", "summary_ko": "...", "meaning_ko": "..."}'
    )

    try:
        response = ask_llm(prompt)
        result = parse_json_response(response)
    except Exception:
        result = {
            "abstract_ko": f"LLM 번역 실패로 원문을 그대로 표시합니다: {item['summary']}",
            "summary_ko": f"LLM 요약 실패로 원문을 그대로 표시합니다: {item['summary']}",
            "meaning_ko": "LLM 요약 실패로 의미를 판단할 수 없습니다.",
        }

    return result
