# 개발 체크포인트 — 2026-10-23

## 반영 범위

- 원문 전체 구간 추출·수치 맥락 보존·관계와 사례 귀속 검토·재연결 및 관리자 미리보기/적용 경로를 통합했다.
- 공개 사례의 저장형 쉬운 해설, 등록 지식 검색과 문서 직접 이동, 관계·규모·독립 원리 표시를 반영했다.
- 전체 목차 작업본 편집·원문 근거 검토·판본/미리보기 확인·원자적 승인을 기존 검토 계층에 통합했다.
- 목적 중심 비교 초안·등록 대상 확인·공개 사양·조사 왕복·안전한 Markdown과 출처 보존을 통합했다.
- Local/Global 챗 범위와 원문에 근거한 문맥 해설을 유지했다.
- 129개 문헌의 오프라인 시드와 원문 해시·관계/규모 재검토 기록, 기존 DTO/Service 적용 경로를 통한 격리 DB 생성·검증 CLI를 포함했다. 외부 API 응답 기록으로 가장하지 않는다.

RAG 중심의 외부 에이전트 지식 제공은 논의 단계이며 이번 코드에 구현하지 않았다. 운영 DB 적용·서버 재시작·재추출·배포는 이번 저장소 정리에서 수행하지 않았다.

## 검사

기존 `.venv`와 `frontend/node_modules`를 사용했다. 백엔드는 메모리/임시 DB와 모의 모델·외부 응답으로 검사했다. 시드 검증 입력은 기존 격리 DB의 읽기 전용 연결이다. 실제 모델 API를 호출하지 않았다.

- `verify_source_ingestion_grounding.py`, `verify_source_extraction_model.py`, `verify_source_extraction_reconnect.py`: 통과.
- `verify_case_context_explanation.py`, `verify_contextual_explainer.py`, `verify_chatbot_grounding.py`: 통과.
- `verify_review_directive.py`, `verify_review_full_editor.py`: 통과.
- `verify_research_discovery.py`, `verify_research_continuation.py`: 통과.
- 기존 연구 왕복 회귀는 `python scripts/verify_research_discovery.py --regression`으로 실행해 통과했다. 이 진입점이 탐색 계획과 자료 평가의 모의 응답을 공급한다. 공개 티켓 응답에서 내부 초안을 숨기는 현재 계약에 맞게 기존 검사의 patch 목록 기대값을 갱신했다.
- `verify_comparison_flow.py <격리 SQLite 경로>`: 통과. 운영 DB를 입력으로 사용하지 않았다.
- `verify_offline_seed.py --database <격리 SQLite 경로> --seed-dir backend/seeds/offline_sources_20261023 --report <로컬 보고서 경로>`: 통과.
- 프런트의 `verify_case_context_frontend.mjs`, `verify_relation_navigation.mjs`, `verify_wiki_navigation.mjs`, `verify_comparison_frontend.mjs`: 통과.
- `node scripts/verify_wiki_selection.mjs --matcher-only`: 통과. 전체 브라우저 자동 검사는 별도 Playwright 설치가 필요하며 이번 정리에서는 실행하지 않았다.
- Vite 5.4.21 빌드: 통과. 기존 500 kB 초과 번들 경고는 남아 있다.

실제 외부 모델 품질, 외부 서비스 가용성, 운영 PostgreSQL과 배포 환경은 이번 검사에 포함하지 않았다. 추출 정합성 검사와 실제 모델의 의미 정확도 평가는 구별한다.

## 로컬 보존 항목

실제 `.env`·인증정보, DB 및 WAL/SHM, 실행 산출물과 `scratch/` 진단 파일은 Git에 포함하지 않는다. 공개 대상 파일과 기존 미push 이력은 비밀값 패턴 검사 및 독립 읽기 전용 검토를 수행했다. 패턴 검사는 모든 종류의 비밀값 부재를 보증하지 않는다. 로컬 실험·사전 상태 snapshot 브랜치는 최종 통합 결과와 별도로 보존하며 일괄 push하지 않는다.
