"""
LLM 호출을 한 곳에서 담당하는 모듈.

- LLM_PROVIDER=mock    : API 키 없이 동작하는 규칙 기반 가짜 응답
- LLM_PROVIDER=ollama  (기본값) : 로컬에서 띄운 Ollama 서버 호출
- LLM_PROVIDER=qwen    : 회사에서 받을 Qwen 엔드포인트(OpenAI 호환 API) 호출
- LLM_PROVIDER=cloud   : Anthropic API 호출

다른 모듈은 항상 ask_llm()만 호출하면 되고, provider 전환은
.env의 LLM_PROVIDER 값만 바꾸면 됩니다.
"""

import os
import json
import re

import requests
from dotenv import load_dotenv

load_dotenv()

REQUEST_TIMEOUT = 300  # 로컬 Ollama 추론은 모델 크기/하드웨어에 따라 1~2분 이상 걸릴 수 있음


def ask_llm(prompt: str, system: str = None) -> str:
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if provider == "cloud":
        return _ask_cloud(prompt, system)
    if provider == "ollama":
        return _ask_ollama(prompt, system)
    if provider == "qwen":
        return _ask_qwen(prompt, system)

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


def _ask_ollama(prompt: str, system: str = None) -> str:
    """로컬 Ollama 서버(기본 http://localhost:11434)를 호출합니다."""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "qwen3.5")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = requests.post(
        f"{base_url}/api/chat",
        json={"model": model, "messages": messages, "stream": False},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def _ask_qwen(prompt: str, system: str = None) -> str:
    """회사에서 제공하는 Qwen 엔드포인트(OpenAI 호환 chat/completions)를 호출합니다."""
    base_url = os.getenv("QWEN_BASE_URL", "").rstrip("/")
    api_key = os.getenv("QWEN_API_KEY", "")
    model = os.getenv("QWEN_MODEL", "qwen3.5-72b-instruct")

    if not base_url or not api_key:
        raise RuntimeError(
            "LLM_PROVIDER=qwen이지만 QWEN_BASE_URL/QWEN_API_KEY가 .env에 설정되어 있지 않습니다."
        )

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = requests.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": model, "messages": messages},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


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


_TITLE_PATTERN = re.compile(r"TITLE: (.+)")
_SUMMARY_PATTERN = re.compile(r"SUMMARY: (.+)")


def _mock_summarize(prompt: str) -> str:
    title_match = _TITLE_PATTERN.search(prompt)
    summary_match = _SUMMARY_PATTERN.search(prompt)
    title = title_match.group(1).strip() if title_match else ""
    summary = summary_match.group(1).strip() if summary_match else ""

    short = summary[:150] + ("..." if len(summary) > 150 else "")
    summary_ko = f"[mock 요약] '{title}' 항목의 원문 초록: {short}" if short else "[mock 요약] 요약할 초록이 없습니다."
    meaning_ko = "[mock 의미] 실제 의미 판단은 mock 모드에서 제공되지 않습니다."

    return json.dumps({"summary_ko": summary_ko, "meaning_ko": meaning_ko}, ensure_ascii=False)
