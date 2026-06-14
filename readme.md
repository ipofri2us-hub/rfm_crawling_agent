echo "# rfm_crawling_agent" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/ipofri2us-hub/rfm_crawling_agent.git
git push -u origin main



rfm_crawling_agent/
├── config/
│   └── settings.yaml          # 화이트리스트 연구실, 키워드, 하드웨어 스펙, 임계치
├── data/
│   ├── rfm_agent.db            # SQLite (자동 생성)
│   ├── failure_history/        # RAG 시드 문서 (실패 이력 예시 markdown 3~5개)
│   └── reports/                # 주간 리포트 markdown 출력
├── src/
│   ├── llm/
│   │   └── provider.py         # mock/local/cloud LLM 호출 추상화 (.env 기반)
│   ├── collectors/
│   │   ├── arxiv_collector.py      # arXiv API (인증 불필요)
│   │   ├── github_collector.py     # GitHub Search API (star 증가량, 화이트리스트 레포)
│   │   └── huggingface_collector.py # HF Hub API (신규 모델/데이터셋)
│   ├── pipeline/
│   │   ├── normalize.py        # 중복제거/메타데이터 정규화
│   │   ├── domain_filter.py    # AI: VLA/모방학습/매니퓰레이션 적합성 판단
│   │   ├── credibility.py       # 화이트리스트/star 기반 신뢰도 가중치
│   │   ├── hw_compat.py         # 하드웨어 스펙(VRAM/레이턴시) 1차 컷오프
│   │   ├── rag_gating.py        # Chroma 기반 과거 실패이력 대조 게이팅
│   │   ├── predictor.py         # 성공률/Hz 정량 예측 (LLM, "추정치" 명시)
│   │   └── report.py            # 최종 리포트 생성 + 검증 체크리스트 포함
│   ├── db/
│   │   ├── schema.py            # SQLite 테이블 정의 + init
│   │   └── store.py             # CRUD 헬퍼
│   ├── notify/
│   │   └── senders.py           # Slack webhook / Notion API 전송 (미설정시 로컬 저장만)
│   └── main.py                  # 파이프라인 오케스트레이터 (CLI)
├── .env.example
└── requirements.txt             # 기존 파일 정리 (불필요 day1~5 전용 패키지 제거, 필요 패키지 추가)