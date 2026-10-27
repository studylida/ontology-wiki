# LightRAG 제거 상태 — 2026-10-27

사용자는 LightRAG의 완전 제거를 지시했다. **서비스 연결과 전용 DB 제거는 완료했지만 전용 파일 삭제는 자동 승인 정책에 차단돼 남아 있다.** 완전한 파일 삭제 완료로 보고하지 않는다.

## 완료한 제거

- 검색 서비스의 LightRAG 생성·호출·후보 연결·snapshot 분기와 전용 문헌 저장소 조회 함수를 제거했다. 벡터·문자 검색, CrossEncoder, Extended 내부 질의·주변 조건 보충, 권한·인용·기존 답변 복원은 유지했다.
- 전용 통합 모듈 3개, 빌드 CLI, 요구사항 파일, 전용 검사와 그래프 설정을 제거했다. 로컬 서버 설정의 `OW_LIGHTRAG_*`와 `OW_RETRIEVAL_GRAPH_MODE`도 삭제했다. 앱 가상환경에는 LightRAG 패키지가 설치돼 있지 않았다.
- 소유 manifest·workspace·전체 relation 및 앱 DB와의 분리를 확인한 뒤 전용 `ontology_lightrag_dev` DB(262,945,815 bytes)를 삭제했다. 앱 PostgreSQL 프로세스와 앱 DB는 유지했다.
- 진행 중 답변·작업이 없음을 확인하고 API와 작업자를 새 코드로 재시작했다. API·웹 HTTP 상태는 정상이다. 관련 검색·답변·평가·실행기 검사 50개가 통과했고 읽기 전용 독립 검토에서 차단 결함을 발견하지 못했다.

## 보존 확인

원문·판본·현재 포인터·내용/메타데이터 해시와 앱 DB의 수량은 제거 전후 일치한다. 문헌 211개, 판본 239개, 승인·색인 완료 199개, 구간 1,571개, 벡터 연결 1,462개, 임베딩 1,325개다. `var/raw`의 원본 파일 236개 모두 존재하고 content-addressed 파일명의 SHA256과 일치한다. Docling·CrossEncoder·RAGChecker는 보존했다.

소규모 비교·비용과 이전 구축의 감사·요약 기록은 `var/rag-evaluation/20261027/lightrag-removal-audit/`에 보존했다. 초기 raw 경로 검사에서 저장 루트를 잘못 해석한 기록은 오류로 명시하고 실제 `var/raw` 기준으로 검증을 다시 했다. 미확인 결과를 성공으로 바꾸지 않았다. 이번 제거 과정에서 새 모델 호출은 없었다.

## 자동 승인 정책으로 남은 파일

다음 5개 대상을 소유·절대 경로로 확인했지만 파일 삭제 명령이 실행 전에 `blocked by policy`로 거절됐다. 다른 도구·언어로 우회하지 않았다. 상세한 정책 사유는 제공되지 않았다.

- `var/lightrag/` — 기존·실험 그래프 파일과 중단 checkpoint, 23,608,733 bytes.
- `var/corpus-quality/20261026T073106Z/review/lanes/lightrag-poc/.venv/` — 격리 SDK 런타임, 285,746,580 bytes.
- 같은 PoC 폴더의 `storage/`, `storage-v2/` — 과거 그래프·응답 캐시·벡터, 합계 1,836,865 bytes.
- 같은 PoC 폴더의 `experiment.py` — 이전 독립 실행 스크립트, 5,833 bytes.

합계 311,198,011 bytes다. 이 파일들은 현재 서비스 경로에서 참조하지 않는다. LightRAG 전용 프로세스는 0개다. 별도로 `backend/knowledge/integrations/__pycache__/`의 LightRAG `.pyc` 3개와 `backend/tests/__pycache__/`의 전용 검사 `.pyc` 1개도 삭제가 차단됐다. 개별 파일의 정확한 LiteralPath로 한정한 요청도 동일하게 거절됐다.

정확한 파일 경로·전후 대조·거절 기록은 `var/rag-evaluation/20261027/lightrag-removal-audit/removal-report.json`에 있다. 위 전용 파일과 캐시의 물리적 정리는 아직 완료되지 않았다. 실제 모델로 답변을 다시 생성하는 검사는 이번 제거 작업에서 수행하지 않았다.
