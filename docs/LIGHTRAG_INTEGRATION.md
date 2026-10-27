# LightRAG 검색 연결

LightRAG는 승인된 공용 문헌에서 추가 근거 구간을 찾는 선택적 검색 경로다. 최종 답변 생성과 인용은 기존 서비스가 맡는다. 그래프의 요약 문장을 원문인 것처럼 전달하지 않고, LightRAG가 돌려준 구간을 저장된 원문 구간 ID에 연결한다.

## 저장과 실행

- Python 3.12 별도 환경에서 `backend/requirements-lightrag.txt`를 설치한다. 서비스 환경은 LightRAG 전체를 import하지 않고 작은 subprocess 어댑터를 사용한다.
- 고정 버전은 `lightrag-hku==1.5.7`이다. 공식 SDK의 `ainsert_custom_chunks`로 기존 문헌 구간을 입력하고 `aquery_data`로 답변 생성 전의 검색 결과를 받는다.
- 저장소는 `PGKVStorage`, `PGVectorStorage`, `PGDocStatusStorage`, `PGTableGraphStorage`다. `PGTableGraphStorage`는 PostgreSQL 일반 테이블을 사용하므로 Apache AGE 설치가 필요하지 않다.
- 그래프는 기존 앱 DB와 다른 `ontology_lightrag_dev`에 둔다. 문헌 원본, 앱 판본, 승인 기록, 기존 임베딩은 변경하지 않는다.
- 생성·임베딩 클라이언트는 기존 서비스의 공급자 어댑터를 재사용해 실제 사용량과 추정 비용을 기록한다. API 키는 서버 환경에서만 읽고 파일이나 stdout에 넣지 않는다.

## 원문과 판본의 연결

`capture_graph_snapshot(session, authorized_revision_ids, embedding_profile_id)`가 빌드와 검색에서 같은 확인을 수행한다. 모든 요청 ID가 현재 승인·활성·색인 완료인 공용 판본인지 재확인하고, 다음 정보를 해시에 포함한다.

- 원문 내용 해시, 문헌 ID·제목 해시, 판본 ID와 현재 활성 판본.
- 메타데이터 버전·해시, 자료 형태, 공개 범위·승인·철회 상태.
- 파서·청킹 프로필, 구간 ID·입력 해시·본문 해시·제외 상태, 임베딩 프로필.

그래프 입력에 사용한 `embeddingText`와 LightRAG에 실제 저장된 구간 내용이 일치하는지 빌드 단계에서 대조한다. 동일 판본 안의 같은 내용이 하나로 합쳐질 수 있으므로 매핑은 하나의 LightRAG 구간에 여러 원문 구간을 연결할 수 있다. 검색 결과도 ID와 내용 해시가 모두 일치할 때만 원문 구간 ID로 반환한다. 출처가 불명확한 합성 설명은 이 매핑을 통과하지 못한다.

각 빌드는 새 workspace를 사용한다. 모든 대상 문헌과 구간을 처리하고 현재 문헌 상태를 다시 확인한 뒤 `active.json`을 원자적으로 교체한다. 실패·취소된 빌드는 활성 포인터를 바꾸지 않는다. 실패 자료와 사용량은 빌드 디렉터리에 남겨 재시도할 수 있다.

예외적으로 아직 활성화되지 않은 중단 빌드는 기존 승인 판본·본문·구간·프로필이 모두 같고 새로운 승인 판본만 추가됐을 때 같은 workspace에서 확장할 수 있다. 활성 workspace에는 추가하지 않는다. 같은 빌드의 CLI를 동시에 여러 개 실행하지 않는다.

검색 요청의 허용 집합과 그래프 snapshot이 정확히 같아야 한다. 자료가 철회되거나 같은 판본의 출처가 수정돼도 이전 그래프는 사용할 수 없다. 필터로 좁힌 검색 범위가 그래프 snapshot과 다르면 기존 검색을 사용하고 그래프를 사용할 수 없었다는 진단을 남긴다. 개인 첨부와 대화는 그래프 입력에 넣지 않는다. 호출 서비스는 그래프 검색 이후에도 DB snapshot을 다시 대조하고 현재 권한을 검사해야 한다.

## 빌드 명령

```powershell
.venv\Scripts\python.exe scripts\v2\build_lightrag_index.py `
  --runtime-python <LightRAG 가상환경의 절대 python.exe 경로> `
  --index-path var\lightrag `
  --source-manifest var\rag-evaluation\20261027\baseline\corpus-manifest.json
```

`--export-only`는 문헌과 구간을 고정해 저장하고 모델을 호출하지 않는다. 기존 빌드를 이어갈 때는 같은 `--source-manifest`와 `--resume <builds 아래의 실행 디렉터리>`를 사용한다. source manifest를 생략하면 실행 시점의 모든 승인·활성 문헌을 사용한다. `--include-title`은 작은 기능 시험용이며, 부분집합 시험을 전체 문헌 품질 평가로 표현하지 않는다.

신규 문헌만 추가된 중단 빌드는 `--resume <실행 디렉터리> --extend`로 확장한다. 먼저 `--export-only`를 함께 사용하면 검증과 감사 파일 작성까지만 한다. 원래 `build-request.json`은 보존하며, 별도 `extension-<UUID>.json`에 확장 요청과 이전·새 fingerprint, 추가 판본 ID, 원본·직전 요청·확장 요청 해시를 함께 원자적으로 저장한다. 그 뒤에는 `--resume <실행 디렉터리> --request-file <extension JSON의 전체 경로>`로 같은 확장 요청을 이어간다. 확장 파일과 원본의 해시가 달라졌거나, 기존 행이 바뀌거나 삭제됐거나, 임베딩 프로필이 달라지면 거부한다. `--index-path`는 해당 실행 디렉터리를 포함하는 원래 index 경로와 같아야 한다.

기본 모델 호출 상한은 1,000회, 빌드 실행 시간 상한은 3,600초이며 임베딩 입력 수를 임의로 100개로 제한하지 않는다. 사용량은 각 빌드의 `usage.json`, 완료 문헌은 `progress.json`, 처리 결과는 `result.json`에 기록한다. 이어서 실행할 때도 이전 호출 비용과 상한을 보존한다. 검색 시 사용량 기록에는 질문 원문을 저장하지 않는다. 중단된 호출은 확인되지 않은 비용으로 남긴다.

`elapsedSeconds`는 해당 프로세스 실행의 소요 시간이다. 중단 뒤 재개한 경우 이전 실행 시간까지 합산한 값으로 보고하지 않는다. 비용의 `knownCostUsd`는 확인된 부분만 합산하므로, `unknownCostCalls`가 있으면 전체 비용을 확정할 수 없다.

재개할 때 `--max-model-calls`를 생략하면 원래 빌드 상한을 유지한다. 명시하면 해당 재개 실행의 누적 호출 상한으로 적용되며 `summary.json`에 기록한다. 원래 문헌 snapshot과 `build-request.json`은 변경하지 않는다.

`--generation-concurrency 8`은 SDK의 공식 `llm_model_max_async` 설정으로 문헌 안의 추출·병합 모델 호출을 최대 8개까지 동시에 처리한다. 생략 시 기존 실험과 같은 2개다. 구간·본문·출력 토큰 범위는 바꾸지 않는다. 고정 SDK 1.5.7의 `ainsert_custom_chunks`는 workspace의 busy 예약으로 동시 문헌 삽입을 명시적으로 거부하므로 문헌은 순서대로 넣고 `max_parallel_insert=1`을 유지한다. 문헌 안의 엔티티·관계 병합은 workspace별 엔티티 키 잠금과 SDK의 모델 동시 호출 제한을 따른다. 임베딩 동시 호출 상한은 2개를 유지한다. `usage.json`의 `callErrors`와 각 오류의 `upstreamStatus`로 429 등 공급자 오류를 확인할 수 있으며, 실패하면 새 인덱스를 활성화하지 않고 더 낮은 동시 호출 상한으로 이어서 실행할 수 있다.

실패한 작업의 sibling 요청도 비용 집계에 포함되도록 모델·임베딩 큐를 종료한 다음 사용량을 최종 집계한다. SDK의 storage finalization만으로 모델 작업 큐가 종료되지는 않는다. 8개 동시 호출 중 1개가 실패하고 7개가 취소되는 회귀 검사에서 반환 사용량과 파일 사용량 모두 8회를 보존한다.

## 검증

`backend/tests/test_lightrag_adapter.py`는 메타데이터 정정·제외 구간·철회·판본 변화, 정확한 내용 매핑, 실패한 활성화의 이전 인덱스 보존, 검색 취소 때 사용량 보존을 검사한다. PostgreSQL 검사는 기존 테스트의 격리 스키마를 사용한다.

SDK 검색은 `hybrid`, 내부 재정렬 끔, 최종 답변 생성 생략으로 실행한다. 검색 시 SDK의 질의 캐시도 꺼 질문·대화 원문이 공용 그래프 저장소에 남지 않게 한다. 승인 문헌의 그래프 구축 캐시는 이어서 처리하기 위해 유지한다. 검색 결과는 기존 후보와 합쳐 공통 CrossEncoder에서 한 번 재정렬한다. 그래프 구축 비용과 질문별 검색 비용은 별도로 비교한다. 이 도구가 항상 더 나은 답변을 만든다는 가정은 두지 않는다.

2026-10-27 고정 평가 문헌 50개의 실제 구축은 기존 구간 147개를 모두 처리했고 PostgreSQL에 노드 1,442개와 관계 1,625개를 저장했다. 전체 구축 호출은 375회, 확인된 누적 추정 비용은 $0.200248725이며 이전 중단 호출 2회의 비용은 미확인이다. 재개 실행 시간 790.157초는 중단 전 시간까지 합산한 값이 아니다. 이 인덱스로 TSV·와이어 본딩 비교 질문을 한 번 검색했을 때 14개 구간 모두 기존 구간 ID와 내용이 일치했으며, 5.656초·2회 모델 호출·추정 비용 $0.00017146을 기록했다. 이 검사는 검색 연결 확인이며 최종 답변 품질 평가는 별도다. 실행 근거는 `var/lightrag/builds/88961b049f57475eadcce720a5a3293c/result.json`과 `var/lightrag/baseline-query-smoke.json`에 있다.

## 출처와 제한

- [LightRAG 공식 저장소](https://github.com/HKUDS/LightRAG), MIT 라이선스.
- 현재 연결은 고정된 승인 snapshot을 대상으로 한다. 원문 변경 뒤 자동 증분 그래프 갱신 스케줄러는 아직 없으며, 새 빌드가 끝날 때까지 기존 검색이 동작한다.
- 구간 기반 그래프는 원문의 표·그림에서 추출하지 못한 내용을 복원하지 않는다. 입력 자료의 `documentForm`과 실제 읽은 범위를 유지한다.
