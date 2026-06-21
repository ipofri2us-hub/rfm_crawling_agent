"""세미나 노트북(docs/seminar.ipynb)을 생성하는 빌드 스크립트.

내용을 코드로 관리해서 마크다운/코드 셀을 안전하게(이스케이프 걱정 없이)
다시 만들 수 있게 합니다. 노트북 자체를 직접 손으로 고칠 필요는 없고,
이 스크립트만 고친 뒤 다시 실행하면 됩니다.
"""

import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text.strip() + "\n"))


def code(text):
    cells.append(nbf.v4.new_code_cell(text.strip() + "\n"))


# ------------------------------------------------------------------
# 0. 타이틀 / 세미나 소개
# ------------------------------------------------------------------
md(r"""
# 🤖 RFM Crawling Agent — "에이전트가 뭔가요?" 세미나

**대상**: 에이전트를 처음 접하는 팀원 (코딩 경험은 있지만 "AI 에이전트"는 처음)
**목표**:
1. "에이전트"라는 단어가 실제로 무슨 뜻인지 감을 잡는다
2. 그 개념이 **이 프로젝트의 코드 한 줄 한 줄**에 어떻게 대응되는지 직접 확인한다
3. 세미나가 끝나면 `agent/` 폴더의 파일들을 혼자 열어봐도 무섭지 않다

> 💡 이 노트북은 **위에서 아래로 셀을 순서대로 실행**하면서 따라오는 것을 추천합니다.
> 코드 셀은 전부 `LLM_PROVIDER=mock` 모드라 API 키 없이, 인터넷 없이도 그대로 동작합니다.
> (실제 운영 환경은 로컬 Ollama로 띄운 Qwen3.5를 기본값으로 씁니다 — 6번 섹션에서 다룹니다.)
""")

# ------------------------------------------------------------------
# 1. 에이전트란 무엇인가 (일반 개념)
# ------------------------------------------------------------------
md(r"""
## 1. 그래서 "에이전트"가 뭔가요?

한 줄 정의:

> **에이전트 = 스스로 "관찰 → 판단 → 행동"을 반복하면서 목표를 달성하는 프로그램**

평범한 스크립트와 다른 점은, 중간에 **판단(Decide)** 단계를 사람이 미리 다 정해두지 않고
**LLM(또는 규칙)이 그 순간 데이터를 보고 결정**한다는 것입니다.

```mermaid
flowchart LR
    P["👀 Perceive\n관찰\n(데이터를 가져온다)"] --> D{"🧠 Decide\n판단\n(LLM/규칙이 결정한다)"}
    D --> A["🛠️ Act\n행동\n(저장/알림/다음 단계 호출)"]
    A --> P
```

- **Perceive(관찰)**: 이 프로젝트에서는 arXiv/GitHub/HuggingFace에서 새 글/레포를 긁어오는 것
- **Decide(판단)**: "이게 우리 연구랑 관련 있나?", "우리 GPU로 돌아가나?", "예전에 실패했던 거 아닌가?"
- **Act(행동)**: DB에 저장하고, 통과한 것만 리포트로 만들어 Slack에 보내는 것

즉 이 프로젝트는 **"매주 논문 찾아보기"라는 사람의 반복 업무를
관찰-판단-행동 루프로 그대로 옮겨놓은 에이전트**입니다.
""")

# ------------------------------------------------------------------
# 2. 이 에이전트는 무엇을 하나
# ------------------------------------------------------------------
md(r"""
## 2. 이 에이전트는 구체적으로 무엇을 하나요?

매주 쏟아지는 로봇 파운데이션 모델(RFM, VLA/모방학습/매니퓰레이션) 관련 논문/레포를
**자동으로 수집 → AI가 우리 상황에 맞는지 판단 → 리포트로 정리**해줍니다.

사람이 매주 하던 일 5가지를 코드로 옮긴 것뿐입니다:

| 사람이 하던 일 | 코드에서는 |
|---|---|
| arXiv/GitHub/HuggingFace 일일이 확인 | `collectors.py` |
| "우리 VLA 연구와 관련 있나?" 판단 | `filters.domain_filter` (LLM) |
| "우리 GPU(VRAM)로 돌릴 수 있나?" 판단 | `filters.hw_compat_check` (규칙) |
| "예전에 비슷한 거 해봤다가 실패하지 않았나?" 기억 | `rag.py` (벡터 검색) |
| 결과를 정리해서 보고 | `report.py` |
""")

# ------------------------------------------------------------------
# 3. 전체 흐름 (메인 플로차트)
# ------------------------------------------------------------------
md(r"""
## 3. 전체 흐름 — 이 그림 하나만 기억하면 됩니다

```mermaid
flowchart TD
    A["1️⃣ 수집\ncollectors.py\narXiv/GitHub/HF"] --> B{"2️⃣ 도메인 적합성?\nfilters.domain_filter (LLM)"}
    B -- "관련 없음" --> D1[("DB\nstatus=dropped")]
    B -- "관련 있음" --> C["신뢰도 + 하드웨어 체크\nfilters.py (규칙 기반)"]
    C --> E{"3️⃣ RAG 게이팅\n과거 실패와 비슷한가?\nrag.py"}
    E -- "비슷함 → 위험" --> D2[("DB\nstatus=rejected")]
    E -- "안 비슷함 → 안전" --> F["4️⃣ 초록 요약\nsummarizer.py (LLM)"]
    F --> D3[("DB\nstatus=accepted")]
    D1 & D2 & D3 --> G["5️⃣ 리포트 생성\nreport.py → Markdown + Slack"]
```

이 그림이 그대로 [main.py](../main.py)의 `for item in items:` 루프 안에 코드로 적혀 있습니다.
**main.py를 열어서 위에서 아래로 읽으면 이 그림이 그대로 보입니다.** 지금 바로 옆에 띄워두세요.
""")

# ------------------------------------------------------------------
# 4. 폴더 구조
# ------------------------------------------------------------------
md(r"""
## 4. 폴더 구조

```text
rfm_crawling_agent/
├── main.py              # 진입점 - 전체 파이프라인을 순서대로 호출
├── config.yaml          # 설정 (키워드, 화이트리스트, 하드웨어 스펙 등)
├── .env.example         # 환경변수 예시 (LLM_PROVIDER 등)
├── agent/
│   ├── llm.py           # ① mock/ollama/qwen/cloud LLM 호출
│   ├── collectors.py    # ② arXiv/GitHub/HuggingFace 수집
│   ├── filters.py        # ③ 도메인 판단 + 신뢰도 + 하드웨어 컷오프
│   ├── rag.py            # ④ 과거 실패이력 RAG 게이팅
│   ├── summarizer.py      # ⑤ 초록 한국어 요약
│   ├── db.py              # ⑥ 결과 저장/조회 (LanceDB)
│   └── report.py          # ⑦ 리포트 생성/Slack 전송
└── data/
    ├── failure_cases/     # RAG가 참조하는 "과거 실패 사례" 문서
    ├── lancedb/            # 자동 생성되는 DB 파일
    └── reports/            # 자동 생성되는 주간 리포트
```

**핵심 설계 원칙**: 파일 하나 = 역할 하나. `main.py`가 이 파일들을 순서대로 부르기만 합니다.
""")

# ------------------------------------------------------------------
# 5. 실습 준비 (setup 코드 셀)
# ------------------------------------------------------------------
md(r"""
## 5. 실습 준비

아래 셀을 실행해서 프로젝트 루트를 import 경로에 추가하고, LLM을 `mock` 모드로 고정합니다.
(`mock` 모드는 API 키 없이도 키워드 규칙으로 그럴듯한 응답을 만들어주는 가짜 LLM입니다.)
""")

code(r"""
import os
import sys

PROJECT_ROOT = os.path.abspath("..")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ["LLM_PROVIDER"] = "mock"  # API 키 없이 실습하기 위한 설정

from agent import collectors, filters, rag, summarizer, llm  # noqa: E402

print("준비 완료! LLM_PROVIDER =", os.environ["LLM_PROVIDER"])
""")

# ------------------------------------------------------------------
# 6. 핵심 개념 1: LLM provider 4가지 (mock/ollama/qwen/cloud)
# ------------------------------------------------------------------
md(r"""
## 6. 핵심 개념 ① — LLM 호출 방식이 4가지나 있다 (mock/ollama/qwen/cloud)

```mermaid
flowchart TD
    M["다른 모듈\n(filters.py, summarizer.py 등)"] --> F["ask_llm(prompt)"]
    F --> Q{"환경변수\nLLM_PROVIDER"}
    Q -- "mock" --> Mock["🎭 _ask_mock()\n키워드 규칙으로\n가짜 JSON 생성"]
    Q -- "ollama (기본값)" --> Ollama["💻 _ask_ollama()\n로컬 Ollama 서버\n(Qwen3.5)"]
    Q -- "qwen" --> Qwen["☁️ _ask_qwen()\n회사 Qwen 엔드포인트\n(OpenAI 호환 API)"]
    Q -- "cloud" --> Cloud["☁️ _ask_cloud()\n실제 Claude API 호출"]
    Mock --> R["같은 모양의 JSON 응답"]
    Ollama --> R
    Qwen --> R
    Cloud --> R
```

- **왜 필요한가?** API 키 없이도 전체 파이프라인이 끝까지 동작해야 개발/테스트가 쉽습니다. 그래서 mock이
  있고, 실제 판단은 로컬에서 돌리는 Ollama(Qwen3.5)를 기본값으로 씁니다. 회사에서 Qwen 엔드포인트를
  받으면 `LLM_PROVIDER=qwen`으로 바꾸기만 하면 됩니다.
- **다른 모듈은 어떤 provider인지 전혀 모릅니다.** 항상 `ask_llm()`만 호출합니다 — 이게 "추상화"입니다.
- ⚠️ Ollama/Qwen 같은 실제 모델은 로컬 PC 추론 기준 **요청당 70~120초** 걸릴 수 있습니다(직접 측정한
  값). 그래서 이 노트북의 실습은 `mock`으로 고정해서 빠르게 진행합니다.

직접 호출해볼까요? ([agent/llm.py](../agent/llm.py))
""")

code(r"""
prompt = (
    "TASK: domain_filter\n"
    "TITLE: Diffusion Policy for Robot Manipulation\n"
    "SUMMARY: A vision-language-action model for imitation learning on robot arms.\n"
)
response = llm.ask_llm(prompt)
print("mock LLM 응답:", response)
""")

# ------------------------------------------------------------------
# 7. 핵심 개념 2: 공통 스키마
# ------------------------------------------------------------------
md(r"""
## 7. 핵심 개념 ② — 모든 항목은 같은 모양의 dict (공통 스키마)

[agent/collectors.py](../agent/collectors.py)는 arXiv/GitHub/HuggingFace 결과를 모두 동일한 형태로 통일합니다.
이후 단계들은 이 dict에 `domain`, `rag_gate`, `ai_summary` 같은 키를 하나씩 **추가**해 나갑니다.

실습에서 쓸 샘플 항목 2개를 만들어봅니다 — 하나는 "통과할 만한" 항목, 하나는 "걸러질 만한" 항목입니다.
""")

code(r"""
good_item = {
    "title": "ARISE-Initiative/diffusion-policy-vla",
    "summary": (
        "A new vision-language-action (VLA) model for imitation learning "
        "robot manipulation. 3B parameters, runs at high control hz."
    ),
    "url": "https://github.com/ARISE-Initiative/diffusion-policy-vla",
    "source": "github",
    "published_date": "2026-06-15",
    "repo_stars": 480,
}

irrelevant_item = {
    "title": "Awesome CSS Animation Library",
    "summary": "A collection of pure CSS animations for web frontend developers.",
    "url": "https://github.com/example/css-animations",
    "source": "github",
    "published_date": "2026-06-15",
    "repo_stars": 50,
}

good_item
""")

# ------------------------------------------------------------------
# 8. 핵심 개념 3: RAG 게이팅
# ------------------------------------------------------------------
md(r"""
## 8. 핵심 개념 ③ — RAG 게이팅 (과거 실패 기억하기)

```mermaid
sequenceDiagram
    participant Main as main.py
    participant Rag as rag.check_failure_history()
    participant DB as LanceDB (failure_cases 테이블)

    Main->>Rag: 신규 항목(item) 전달
    Rag->>Rag: item 텍스트를 벡터로 변환 (_embed)
    Rag->>DB: 가장 비슷한 과거 실패 사례 검색 (벡터 유사도)
    DB-->>Rag: 거리(distance) + 매칭된 문서
    alt distance가 임계치보다 작음 (비슷함)
        Rag-->>Main: rejected=true, 근거 문서 인용
    else distance가 임계치보다 큼 (안 비슷함)
        Rag-->>Main: rejected=false
    end
```

- `data/failure_cases/*.md`에 과거 실패 사례를 텍스트로 적어둡니다.
- 신규 항목도 같은 방식으로 벡터로 변환 → **가장 가까운(유사한) 과거 실패 사례**를 검색
- 거리(distance)가 임계치(`SIMILARITY_DISTANCE_THRESHOLD = 1.2`)보다 작으면 → "예전에 비슷한 거 해봤다가
  실패했음" → `rejected` 처리

> 이 프로젝트는 임베딩 모델을 따로 다운로드하지 않기 위해, 단어를 해시값으로 변환해
> 벡터를 만드는 아주 단순한 방식(`_embed` 함수)을 사용합니다. 실전에서는 sentence-transformers
> 같은 진짜 임베딩 모델로 교체하면 정확도가 올라갑니다.

현재 등록된 과거 실패 사례 파일들을 먼저 확인해봅시다.
""")

code(r"""
import glob

for path in sorted(glob.glob(os.path.join(rag.FAILURE_CASES_DIR, "*.md"))):
    print("-", os.path.basename(path))
""")

code(r"""
# good_item이 과거 실패 사례와 얼마나 비슷한지 확인해봅시다.
rag.check_failure_history(good_item)
""")

md(r"""
실행해보면 `good_item`(3B 모델, VRAM 문제 없음)이 **`rejected=True`**로 나옵니다 —
"70B급 VRAM OOM" 실패 사례와 distance 1.2 미만으로 잡혔기 때문입니다.

직관적으로는 이상해 보이지만, 위에서 설명한 `_embed()`의 정체를 떠올려보면 당연한 결과입니다:
이 임베딩은 **단어가 겹치는 정도**만 보는 단순한 bag-of-words 방식이라, "VLA / manipulation / policy"
같은 도메인 단어가 많이 겹치면 모델 크기(3B vs 70B)나 실패 원인(VRAM 부족)과 무관하게
"비슷하다"고 판단합니다. **이게 바로 진짜 임베딩 모델로 교체해야 하는 이유**입니다.
""")

# ------------------------------------------------------------------
# 9. 손으로 파이프라인 직접 돌려보기
# ------------------------------------------------------------------
md(r"""
## 9. main.py를 손으로 한 단계씩 따라가 보기

[main.py](../main.py)의 `for item in items:` 루프 안에서 일어나는 일을 그대로,
한 셀씩 실행해서 `good_item`에 키가 하나씩 쌓이는 걸 직접 확인합니다.
""")

code(r"""
# [2/5] 도메인 판단 (LLM)
good_item["domain"] = filters.domain_filter(good_item)
print("도메인 판단 결과:", good_item["domain"])
""")

code(r"""
# config.yaml 로드 (credibility_score, hw_compat_check에 필요)
import yaml

with open(os.path.join(PROJECT_ROOT, "config.yaml"), "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# [3/5] 신뢰도 + 하드웨어 체크 (규칙 기반, LLM 안 씀)
good_item["credibility"] = filters.credibility_score(good_item, config)
good_item["hw_compat"] = filters.hw_compat_check(good_item, config)

print("신뢰도:", good_item["credibility"])
print("하드웨어 호환성:", good_item["hw_compat"])
""")

code(r"""
# RAG 게이팅
good_item["rag_gate"] = rag.check_failure_history(good_item)
print("RAG 게이팅:", good_item["rag_gate"])
""")

code(r"""
# [4/5] 통과했다면 -> 초록 요약 (LLM)
if not good_item["rag_gate"]["rejected"]:
    good_item["ai_summary"] = summarizer.summarize_item(good_item)
    print("요약 결과:")
    print(good_item["ai_summary"])
else:
    print("RAG 게이팅에서 기각되어 요약 단계로 가지 않습니다.")
""")

code(r"""
# 지금까지 쌓인 item 전체 모양을 확인 (실제 main.py가 DB에 저장하는 모양 그대로)
import json

print(json.dumps(good_item, indent=2, ensure_ascii=False))
""")

md(r"""
이제 `irrelevant_item`(CSS 애니메이션 레포)으로도 똑같이 돌려봅시다.
""")

code(r"""
irrelevant_item["domain"] = filters.domain_filter(irrelevant_item)
print("도메인 판단 결과:", irrelevant_item["domain"])
print()
if irrelevant_item["domain"]["is_relevant"]:
    print("-> mock이 '관련 있음'으로 판단했습니다. 아래 설명을 확인하세요.")
else:
    print("-> 관련 없음으로 판단되어 여기서 dropped 처리, 신뢰도/하드웨어/RAG/요약 단계는 건너뜁니다.")
""")

md(r"""
실행해보면 CSS 애니메이션 레포인데도 `is_relevant=True, score=0.7`이 나옵니다. 버그처럼 보이지만
mock 구현([agent/llm.py](../agent/llm.py) `_mock_domain_filter`)의 한계를 보여주는 좋은 예시입니다:

`domain_filter`가 만드는 prompt 안에는 항상 이런 지시문이 들어갑니다 —
`"VLA(Vision-Language-Action), 모방학습, 로봇 매니퓰레이션과 관련 있는지 판단하고..."`.
mock은 **title/summary뿐 아니라 prompt 전체 문자열**에서 키워드를 찾기 때문에,
이 지시문 자체에 들어있는 `"vla"`, `"vision-language-action"` 단어가 매번 잡혀서
최소 score 0.7은 항상 깔고 갑니다. 즉 **mock은 "확실히 관련 없음"을 걸러내는 데는 약합니다.**

→ 그래서 Q&A에서도 다뤘듯, mock은 "파이프라인 구조가 끝까지 도는지" 검증하는 용도이고,
실제 정확한 도메인 판단은 `LLM_PROVIDER=ollama`(로컬 Qwen3.5) 또는 `qwen`(회사 엔드포인트)으로 바꿔서 검증해야 합니다.
""")

# ------------------------------------------------------------------
# 10. main.py 전체 시퀀스
# ------------------------------------------------------------------
md(r"""
## 10. main.py 전체 그림 — 누가 누구를 호출하나

```mermaid
sequenceDiagram
    participant Main as main.py
    participant Col as collectors.py
    participant Filt as filters.py
    participant Rag as rag.py
    participant Summ as summarizer.py
    participant DB as db.py (LanceDB)
    participant Rep as report.py

    Main->>Col: collect_all(config)
    Col-->>Main: items[]

    loop 각 item마다
        Main->>Filt: domain_filter(item)
        alt 관련 없음
            Main->>DB: save_item(item, status="dropped")
        else 관련 있음
            Main->>Filt: credibility_score / hw_compat_check
            Main->>Rag: check_failure_history(item)
            alt 과거 실패와 비슷함
                Main->>DB: save_item(item, status="rejected")
            else 비슷하지 않음
                Main->>Summ: summarize_item(item)
                Main->>DB: save_item(item, status="accepted")
            end
        end
    end

    Main->>DB: get_all_items()
    Main->>Rep: generate_and_save(all_items)
    Rep->>Rep: Markdown 리포트 작성 + Slack 전송
```

이 다이어그램이 [main.py:36-67](../main.py)을 그대로 그림으로 옮긴 것입니다.
코드와 그림을 나란히 띄워두고 한 줄씩 짚어보세요.
""")

# ------------------------------------------------------------------
# 11. 직접 전체 실행
# ------------------------------------------------------------------
md(r"""
## 11. 이제 전체를 진짜로 실행해보기

이 노트북에서는 손으로 한 단계씩 봤지만, 실제로는 터미널에서 한 번에 돌립니다.

```bash
pip install -r requirements.txt
cp .env.example .env          # 기본값은 LLM_PROVIDER=ollama (로컬 Qwen3.5)
python main.py
```

> 로컬 Ollama가 안 떠 있다면 `.env`의 `LLM_PROVIDER=mock`으로 바꿔서 먼저 구조만 확인해도 됩니다.

확인할 것:
1. 콘솔에 `[1/5] 수집 중...` ~ `[5/5] 리포트 생성...` 단계별 로그
2. `data/reports/<오늘날짜>.md` 파일 — accepted/rejected/dropped 항목이 어떻게 나뉘었는지
3. (선택) `data/failure_cases/`에 새 실패 사례를 추가하고 다시 실행 → RAG 기각 결과가 바뀌는지 관찰

> ⚠️ `python main.py`는 실제 `data/lancedb/`(운영 DB)에 데이터를 씁니다.
> 이 노트북의 실습 셀들은 읽기 전용이거나 메모리 안의 dict만 다루도록 만들어서 안전합니다.
""")

# ------------------------------------------------------------------
# 12. 실습 과제
# ------------------------------------------------------------------
md(r"""
## 12. 세미나 실습 과제 (확장 아이디어)

1. **`config.yaml` 튜닝**: `keywords`, `max_params_b`, `github_star_threshold`를 바꿔보고
   리포트 결과가 어떻게 달라지는지 확인
2. **새 실패 사례 추가**: `data/failure_cases/`에 우리 팀의 실제 실패 경험을 markdown으로
   작성 → RAG 게이팅이 실제로 동작하는지 확인 (이 노트북의 8번 셀로 빠르게 테스트 가능)
3. **실제 LLM 전환**: `.env`에서 `LLM_PROVIDER=ollama`(로컬 Qwen3.5) 또는 `qwen`(회사 엔드포인트)으로
   바꾸고 결과 비교 (mock은 키워드 매칭이라 관대한 편)
4. **새 수집 소스 추가**: `agent/collectors.py`에 `fetch_xxx()` 함수를 추가하고
   `collect_all()`에 연결 (공통 스키마만 맞추면 나머지 파이프라인은 그대로 동작)
""")

# ------------------------------------------------------------------
# 13. Q&A
# ------------------------------------------------------------------
md(r"""
## 13. 예상 질문 (Q&A)

**Q. mock LLM은 진짜 AI가 아닌데 왜 필요한가요?**
A. 개발 중에는 API 비용/속도 문제로 매번 실제 LLM을 호출하기 부담스럽습니다. mock으로
파이프라인 구조 자체가 잘 동작하는지 먼저 검증하고, 마지막에 ollama/qwen 같은 실제 LLM으로 바꿔서 정확도를 올립니다.

**Q. LanceDB가 뭔가요? SQLite/Chroma와 뭐가 다른가요?**
A. "일반 데이터 저장(items)"과 "벡터 유사도 검색(failure_cases)"을 **하나의 라이브러리**로
처리할 수 있는 임베디드 DB입니다. 별도 서버 없이 폴더(`data/lancedb/`)에 파일로 저장됩니다.

**Q. RAG 게이팅 임계치(`SIMILARITY_DISTANCE_THRESHOLD`)는 어떻게 정하나요?**
A. 처음에는 감으로 설정(현재 1.2) 후, 실제로 기각되는/통과되는 사례를 보면서 조정합니다.
너무 작으면 거의 다 통과(게이팅 무력화), 너무 크면 거의 다 기각됩니다.

**Q. 예전에는 성공률/Hz 개선 효과까지 예측해줬다던데, 왜 빠졌나요?**
A. 그 예측치는 결국 LLM(또는 mock)의 추정값일 뿐이라 신뢰하기 어려웠고, 검증을 위한 체크리스트도
결국 사람이 시뮬레이터/실로봇으로 직접 채워야 했습니다. 그래서 "근거 없는 숫자 추정"보다,
사람이 원문 초록을 안 읽고도 빠르게 내용을 파악할 수 있는 **한국어 요약**으로 바꿔서
실제로 리포트를 읽는 사람의 판단을 돕는 쪽에 집중했습니다.

**Q. 이게 진짜 "에이전트"인가요? 그냥 if문 모아둔 거 아닌가요?**
A. 핵심은 **판단(Decide) 단계를 LLM에 위임했다는 것**입니다. `domain_filter`나
`summarize_item`은 결과를 사람이 미리 정해둘 수 없고, 그때그때 내용을 보고
LLM이 결정/생성합니다. 그 판단 결과에 따라 다음 행동(저장 위치, 다음 단계 진행 여부)이
자동으로 갈라지는 것 — 그게 "에이전트"와 "스크립트"의 경계선입니다.

**Q. Ollama(로컬)랑 Qwen 엔드포인트(회사)는 뭐가 다른가요?**
A. 둘 다 같은 Qwen 계열 모델이지만 **어디서 도냐**가 다릅니다. Ollama는 내 PC GPU/CPU로
직접 추론하는 거라 키가 필요 없지만 느리고(요청당 70~120초 관찰됨) 내 컴퓨터가 켜져 있어야
합니다. 회사 Qwen 엔드포인트는 서버에서 도는 모델을 API로 부르는 거라 빠르고 항상 켜져
있지만, `QWEN_BASE_URL`/`QWEN_API_KEY` 같은 인증 정보가 필요합니다.
""")

# ------------------------------------------------------------------
# 14. 에이전트의 "툴(Tool)"과 RAG
# ------------------------------------------------------------------
md(r"""
## 14. 에이전트의 "툴(Tool)"이란? — RAG는 그중 하나

일반적으로 LLM 에이전트에서 **"툴(tool)"**이란, LLM이 텍스트 생성만으로는 할 수 없는 일을
대신 해주는 외부 함수/기능을 말합니다 (예: 웹 검색, 계산기, 코드 실행, DB 조회). 에이전트는
"이 상황에서 어떤 툴이 필요하다"고 판단하고, 그 툴을 호출한 결과를 받아 다음 판단에 씁니다.

```mermaid
flowchart LR
    L["🧠 LLM\n(판단)"] -- "이 정보가 필요해" --> T1["🔍 검색 툴"]
    L -- "이 계산이 필요해" --> T2["🧮 계산 툴"]
    L -- "예전 기록이 필요해" --> T3["🗄️ RAG(기억) 툴"]
    T1 & T2 & T3 -- "결과 반환" --> L
```

**RAG(Retrieval-Augmented Generation)는 그중 "기억/검색 툴"입니다** — LLM이 학습 때 보지
못한 데이터(여기서는 우리 팀의 과거 실패 사례)를 그때그때 찾아와서 판단에 반영하게 해줍니다.

이 프로젝트는 LLM이 "어떤 툴을 쓸지"를 스스로 고르지는 않고, `main.py`가 고정된 순서로
툴들을 호출합니다 (더 단순한 형태의 에이전트). 그래도 "각 단계가 무슨 역할의 툴인가"로
보면 코드가 훨씬 명확하게 읽힙니다.

| 툴 | 역할 | 이 프로젝트의 구현 | LLM이 직접 판단? |
|---|---|---|---|
| 수집 툴 | 외부에서 새 데이터를 가져옴 (관찰) | `collectors.py` (arXiv/GitHub/HuggingFace API) | ❌ 규칙 기반 API 호출 |
| 도메인 판단 툴 | "이게 우리 연구와 관련 있나?" 판단 | `filters.domain_filter` | ✅ LLM |
| 신뢰도/하드웨어 체크 툴 | 화이트리스트·star·VRAM 기준 1차 컷오프 | `filters.credibility_score`, `filters.hw_compat_check` | ❌ 규칙 기반 |
| 검색/기억 툴 (RAG) | 과거 실패 사례를 벡터로 검색해 "이미 해봤다가 실패했는지" 확인 | `rag.check_failure_history` | ❌ 검색 자체는 벡터 유사도 계산 |
| 요약 툴 | 원문 초록을 한국어로 요약 | `summarizer.summarize_item` | ✅ LLM |
| 저장 툴 | 판단 결과를 DB에 기록 | `db.save_item` | ❌ 규칙 기반 |
| 보고 툴 | 결과를 사람이 읽을 형태로 정리, Slack 전송 | `report.py` | ❌ 규칙 기반 |

> 💡 ChatGPT의 "웹 검색", "코드 실행" 같은 기능도 똑같은 개념입니다 — LLM이 "이 질문엔 웹 검색이
> 필요하다"고 스스로 판단하면 검색 툴을 호출합니다. 이 프로젝트는 그 판단(어떤 툴을 언제 쓸지)을
> `main.py`가 고정된 순서로 대신 해주는, 더 단순하고 예측 가능한 형태의 에이전트입니다.
""")

# ------------------------------------------------------------------
# 15. 다음 스텝
# ------------------------------------------------------------------
md(r"""
## 15. 다음 스텝

- 발표용 말풍선 대본은 [docs/seminar_script.md](seminar_script.md)를 참고하세요
  (이 노트북의 섹션 순서와 1:1로 맞춰져 있습니다).
- 세미나가 끝난 후에는 실습 과제 1~4번 중 하나를 골라 작은 PR로 만들어보는 것을 추천합니다.
""")

nb["cells"] = cells
nb["metadata"] = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    },
    "language_info": {"name": "python", "version": "3"},
}

with open("seminar.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print("docs/seminar.ipynb 재생성 완료:", len(cells), "cells")
