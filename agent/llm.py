"""
LLM 호출을 한 곳에서 담당하는 모듈.

- LLM_PROVIDER=mock  (기본값) : API 키 없이 동작하는 규칙 기반 가짜 응답
- LLM_PROVIDER=cloud          : Anthropic API 호출

다른 모듈은 항상 ask_llm()만 호출하면 되고, mock/cloud 전환은
.env의 LLM_PROVIDER 값만 바꾸면 됩니다.
"""

import os
import json
import hashlib

from dotenv import load_dotenv

load_dotenv()


def ask_llm(prompt: str, system: str = None) -> str:
    provider = os.getenv("LLM_PROVIDER", "mock").lower()

    if provider == "cloud":
        return _ask_cloud(prompt, system)

    return _ask_mock(prompt)


def _ask_cloud(prompt: str, system: str = None) -> str:
    from anthropic import Anthropic

    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system or "",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


# ------------------------------------------------------------------
# Mock 응답
# 각 모듈은 prompt 맨 앞에 "TASK: xxx" 표시를 붙여서 어떤 작업인지 알려줍니다.
# ------------------------------------------------------------------

_RELEVANT_KEYWORDS = [
    "vla", "vision-language-action", "imitation learning", "manipulation",
    "robot", "policy", "diffusion policy", "action chunking", "grasp", "arm",
]


def _ask_mock(prompt: str) -> str:
    if "TASK: domain_filter" in prompt:
        return _mock_domain_filter(prompt)
    if "TASK: predict" in prompt:
        return _mock_predict(prompt)
    if "TASK: summarize" in prompt:
        return _mock_summarize(prompt)
    return "[mock] 처리할 수 없는 요청입니다."


def _mock_domain_filter(prompt: str) -> str:
    text = prompt.lower()
    matches = [kw for kw in _RELEVANT_KEYWORDS if kw in text]
    is_relevant = len(matches) > 0
    score = round(min(1.0, 0.3 + 0.2 * len(matches)), 2)
    reason = (
        f"키워드 매칭: {', '.join(matches)}"
        if matches
        else "VLA/모방학습/매니퓰레이션 관련 키워드를 찾지 못함"
    )
    return json.dumps(
        {"is_relevant": is_relevant, "score": score, "reason": reason},
        ensure_ascii=False,
    )


def _mock_predict(prompt: str) -> str:
    # 제목 해시값으로 그럴듯한 추정치를 생성하는 mock (실제 의미 없는 값)
    seed = int(hashlib.md5(prompt.encode("utf-8")).hexdigest(), 16)
    success_gain = 3 + (seed % 12)  # 3 ~ 14 (%p)
    hz_gain = 1 + (seed % 8)  # 1 ~ 8 Hz
    return json.dumps(
        {
            "success_rate_gain_pct": success_gain,
            "control_hz_gain": hz_gain,
            "note": "이 값은 LLM 추정치이며 실측으로 검증 전까지 참고용입니다.",
        },
        ensure_ascii=False,
    )


def _mock_summarize(prompt: str) -> str:
    return "[mock 요약] 이번 주 수집된 항목에 대한 자동 요약입니다."
