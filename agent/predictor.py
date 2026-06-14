"""
RAG 게이팅을 통과한 항목에 대해 성공률/제어 주파수 개선 "추정치"를 생성하고,
이를 검증하기 위한 실물 교차검증 체크리스트를 함께 만듭니다.
"""

import json

from agent.llm import ask_llm


def predict_improvement(item: dict) -> dict:
    """LLM에게 성공률/Hz 개선 추정치를 요청합니다.

    반환: {
        "success_rate_gain_pct": float,
        "control_hz_gain": float,
        "note": str,
        "validation_checklist": str,
    }
    """
    prompt = (
        "TASK: predict\n"
        f"TITLE: {item['title']}\n"
        f"SUMMARY: {item['summary']}\n"
        "위 기법을 우리 시스템에 도입했을 때 예상되는 성공률 향상폭(%p)과 "
        "제어 주파수 개선폭(Hz)을 JSON으로만 답하세요: "
        '{"success_rate_gain_pct": number, "control_hz_gain": number, "note": "..."}'
    )
    response = ask_llm(prompt)

    try:
        result = json.loads(response)
    except json.JSONDecodeError:
        result = {
            "success_rate_gain_pct": 0,
            "control_hz_gain": 0,
            "note": f"LLM 응답 파싱 실패: {response}",
        }

    result["validation_checklist"] = _build_checklist(item, result)
    return result


def _build_checklist(item: dict, prediction: dict) -> str:
    return (
        f"[실물 교차검증 체크리스트] '{item['title']}'\n"
        f"- AI 추정치: 성공률 +{prediction.get('success_rate_gain_pct', '?')}%p, "
        f"제어주파수 +{prediction.get('control_hz_gain', '?')}Hz\n"
        "- [ ] 시뮬레이터에서 20회 이상 구동 후 성공률/Hz 실측치 입력\n"
        "- [ ] 실제 로봇(마스터 암)에서 10회 이상 구동 후 성공률/Hz 실측치 입력\n"
        "- [ ] 추정치-실측치 오차를 기록하여 다음 주 예측 보정에 사용\n"
    )
