# Ontology Wiki — 사내 지식 기반 AI 어시스턴트 (재설계 중)

> **제품 목표:** 회사가 보유한 내부 문헌·도메인 지식을 바탕으로 직원의 질문에 사내 맥락을 반영하여 답변한다.

## 먼저 읽을 문서

[목표 아키텍처: docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

이 문서가 앞으로 구현할 서비스의 설계 기준이다. 과거 위키/분석 5파트, Extended, 외부 문헌 조사, 개인 위키 및 과거 답변 이관은 새 제품 범위에서 제외했다. 관리자 기능은 문헌·전처리·색인·진단 중심으로 개편하고, 온톨로지는 선택적 내부 보강 기능으로 둔다. 다이어그램은 후순위의 실패 허용형 렌더러다.

### 현재 코드 상태

- 새 목표 설계는 **아직 구현된 상태가 아니다.** 기존 UI·API·DB와 혼재된 코드가 있으므로 현재 기능을 신규 설계의 완료 증거로 취급하지 않는다.
- 구현 대비 기준은 `68ccd5f3bc98abd480d5a413947974aa02843a66`이며, 이 커밋에는 원문/표/수식 위치 보존과 전처리 품질 보류 개선이 포함된다. 해당 개선의 실제 RAG 답변 품질은 별도로 평가해야 한다.
- 기존 개발 DB의 구 위키/분석 답변, 개인 위키, 레거시 스키마는 새 서비스로 이관할 필요가 없다. **실제 DB·원문 파일은 Git 기록에 포함되지 않으므로 폐기 작업은 대상 환경을 확인한 뒤 별도로 수행한다.**
- 자료 보안·원문 추적·실행 상태는 유지하고, 보조 기능의 실패가 정상 답변을 막지 않도록 설계한다.

### 개발시 참고

새 코드로 개편하기 전 기존 런타임을 검증하려면 PostgreSQL/pgvector, Python 3.12, Node.js를 사용한다. 현재 개발용 명령은 변경될 수 있다.

```bash
python3 scripts/v2/init_dev_env.py
docker compose --env-file .env -f compose.dev.yml up -d db
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-dev.txt
.venv/bin/python scripts/v2/dev.py migrate --database-name ontology_wiki_dev
.venv/bin/python scripts/v2/dev.py serve
# 별도 셸: .venv/bin/python scripts/v2/dev.py worker
# 별도 셸: cd frontend && npm ci && npm run dev
```

기존 명령은 **구형 구현**을 실행한다. 새 DB 초기화·데이터 삭제·운영 배포는 수행하지 않는다. 공급자 키는 환경변수로만 설정하고 Git·화면·로그에 노출하지 않는다.

앞으로의 구현과 검증은 위 목표 아키텍처를 기준으로 단계별로 진행한다. 오래된 보고서는 Git 이력에서 필요할 때만 조회한다.
