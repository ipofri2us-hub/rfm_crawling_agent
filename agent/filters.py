"""
수집된 항목에 대한 AI 판단 단계.

1. domain_filter      : VLA/모방학습/매니퓰레이션 관련 여부 (LLM)
2. credibility_score  : 화이트리스트 연구실 / GitHub star 기반 신뢰도 (규칙 기반)
3. hw_compat_check    : 우리 하드웨어(VRAM) 스펙과의 1차 호환성 컷오프 (규칙 기반)
"""

import re

from agent.llm import ask_llm, parse_json_response


def domain_filter(item: dict) -> dict:
    """LLM에게 VLA/모방학습/매니퓰레이션 관련 여부를 판단시킵니다.

    반환: {"is_relevant": bool, "score": float, "reason": str, "reason_ko": str}
    """
    prompt = (
        "TASK: domain_filter\n"
        f"TITLE: {item['title']}\n"
        f"SUMMARY: {item['summary']}\n"
        "위 항목이 VLA(Vision-Language-Action), 모방학습, 로봇 매니퓰레이션과 관련 있는지 "
        "판단하고 JSON으로만 답하세요. 다른 설명 없이 JSON 한 줄만 출력하세요. "
        "reason과 reason_ko는 각각 줄바꿈이나 마크다운(글머리표, 굵게 등) 없이 한 문장으로만 "
        "작성하세요. reason은 영어로, reason_ko는 그 한국어 번역으로 작성하세요: "
        '{"is_relevant": true/false, "score": 0~1, "reason": "...(English, one sentence)", '
        '"reason_ko": "...(한국어 번역, 한 문장)"}'
    )
    try:
        response = ask_llm(prompt)
    except Exception as e:
        reason = f"LLM call failed, skipping: {e}"
        return {"is_relevant": False, "score": 0.0, "reason": reason, "reason_ko": f"LLM 호출 실패로 건너뜀: {e}"}

    try:
        result = parse_json_response(response)
    except Exception:
        reason = f"Failed to parse LLM response: {response}"
        return {
            "is_relevant": False,
            "score": 0.0,
            "reason": reason,
            "reason_ko": f"LLM 응답 파싱 실패: {response}",
        }

    result.setdefault("reason_ko", result.get("reason", ""))
    return result


def credibility_score(item: dict, config: dict) -> dict:
    """화이트리스트 연구실 여부와 GitHub star 수로 신뢰도를 점수화합니다.

    반환: {"score": float, "is_whitelisted": bool, "reason": str}
    """
    title_lower = item["title"].lower()
    url_lower = item["url"].lower()

    for lab in config.get("whitelist_labs", []):
        org = lab["github_org"].lower()
        if org in title_lower or org in url_lower:
            return {
                "score": 1.0,
                "is_whitelisted": True,
                "reason": f"화이트리스트 연구실 '{lab['name']}' ({org}) 소속/관련 항목",
            }

    stars = item.get("repo_stars") or 0
    threshold = config.get("github_star_threshold", 200)
    score = min(1.0, stars / threshold) if threshold else 0.0

    return {
        "score": round(score, 2),
        "is_whitelisted": False,
        "reason": f"화이트리스트 미포함, star {stars}개 기준 점수 {round(score, 2)}",
    }


# 모델명/설명에서 파라미터 규모를 추출하기 위한 패턴 (예: "7B", "1.5B", "70b")
_PARAM_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*[bB]\b")


def hw_compat_check(item: dict, config: dict) -> dict:
    """제목/요약에서 모델 파라미터 규모(B)를 추출해 우리 GPU VRAM과 비교합니다.

    반환: {"compatible": bool, "estimated_params_b": float | None, "reason": str}
    """
    text = f"{item['title']} {item['summary']}"
    match = _PARAM_PATTERN.search(text)

    if not match:
        return {
            "compatible": True,
            "estimated_params_b": None,
            "reason": "파라미터 규모를 추출하지 못해 1차 컷오프를 적용하지 않음 (사람 검토 필요)",
        }

    params_b = float(match.group(1))

    max_params_b = config["hw_specs"].get("max_params_b")
    if max_params_b is not None and params_b > max_params_b:
        return {
            "compatible": False,
            "estimated_params_b": params_b,
            "reason": (
                f"추정 파라미터 {params_b}B -> 설정된 상한({max_params_b}B) 초과로 "
                "물리적으로 불가능 (1차 컷오프)"
            ),
        }

    # 매우 단순한 추정: FP16 기준 파라미터 1B당 약 2GB + 추론 오버헤드 20%
    estimated_vram_gb = params_b * 2 * 1.2
    vram_limit = config["hw_specs"]["vram_gb"]
    compatible = estimated_vram_gb <= vram_limit

    return {
        "compatible": compatible,
        "estimated_params_b": params_b,
        "reason": (
            f"추정 파라미터 {params_b}B -> 약 {estimated_vram_gb:.1f}GB VRAM 필요 "
            f"(보유 {vram_limit}GB) -> {'가능' if compatible else '물리적으로 불가능'}"
        ),
    }
