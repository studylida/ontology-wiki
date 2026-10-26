# 실제 API 검증 기록 — 2026-10-26

## 확인한 범위

사용자가 지정한 **`gpt-6-luna` / `medium`**으로 위키 답변, 같은 대화의 분석 답변, 개인 위키 생성·병합, 외부 문헌의 확보·대화 이관·답변 활용을 실제 실행했다. 별도의 브라우저 실행에서는 실제 스트림을 받는 도중 새로고침하고 취소한 뒤, 부분 답변과 취소 상태가 복원되는 것도 확인했다.

검증 중 발견한 관계 추출·Extended 종료 상태·외부 문헌 설명 형식의 결함은 수정 전 결과를 남기고 후속 실제 호출로 다시 확인했다. **이 기록은 소수 실제 사례의 동작 확인이며, 반도체 전문가의 정답 검증이나 전체 서비스의 의미 정확도·성능 평가가 아니다.** 세부 의미 검토와 파일 지문은 [semantic-review.md](verification/live/semantic-review.md)에 있다.

### 환경과 자료 경계

- 초기 fixture 개발 DB와 분리한 **`ontology_wiki_live_dev`**에서 실행했다. 운영 DB 이전·운영 배포·운영 트래픽 검증을 수행한 기록이 아니다.
- 초기 대화 근거는 제공된 공개 문헌 3건이다: SK하이닉스 미래인재 CLASS, SK하이닉스 하이피디아 TSV, 삼성 반도체 패키징 교육 자료. 초기 색인 작업은 기존 벡터를 3·3·5개 재사용해 11개 구간을 색인했으며, 해당 세 작업의 `embedded=0`이다.
- 외부 조사 왕복에서는 사용자가 지정한 공개 Lam Research 기술 용어집을 추가했다. 부분적으로 읽은 자료라는 표시를 유지했다.
- 후속 온톨로지 검증은 별도의 새 개발 스키마에서 수행했다. 기존 공용 데이터에 결과를 덮어쓰지 않았고, 계정 자격 증명이나 임베딩을 복사하지 않았다.
- 브라우저의 취소 검증은 별도 새 대화와 공개 문헌 3건만 사용했다. 비공개 첨부·이전 대화·개인 위키 자동 정리·Extended는 사용하지 않았다.
- 공개 기록에는 API 키·인증 토큰·프록시 자격 증명·원본 HTML·전체 원문 snapshot을 넣지 않는다. 문헌 제목·URL·판본 ID·실행 ID·필요한 검증 집계로 추적한다.

## 1. 실제 모델·effort와 응답 스트림

[wiki-initial.json](verification/live/wiki-initial.json), [analysis-comparison.json](verification/live/analysis-comparison.json), [research-answer.json](verification/live/research-answer.json)의 공급자 usage component에는 `model=gpt-6-luna`, `source=provider`, `modelSource=provider`, `fixtureCalls=0`이 있다. 응답 메타데이터의 `model`도 같으며 `reasoning.effort=medium`을 반환했다. 요청 설정만 보고 실제 호출 모델을 추정한 것이 아니다.

완료된 아래 여섯 답변의 SSE에는 실제 `text.delta`와 마지막 `run.completed`가 있었고, 기록된 sequence가 엄격히 증가했다. 초기 위키에는 1,233개의 `text.delta` 이벤트가 관측됐다. 이 숫자는 이벤트 개수이며 토큰 사용량이 아니다.

### 측정한 시간

아래 값은 각 파일의 **서버 측 `final.metrics`에 저장된 밀리초(ms)**다. 한 번씩 실행한 관측값이며 평균·백분위·운영 성능 보장이 아니다. `firstTextMs`는 실제 답변 텍스트가 처음 발생한 시점이며, 공급자 연결 또는 첫 이벤트 시점인 `providerEventMs`와 구분했다.

| 실제 실행 | 검색 `retrievalMs` | 첫 실제 답변 `firstTextMs` | 생성 `generationMs` | 전체 `totalMs` |
|---|---:|---:|---:|---:|
| 초기 위키 | 653.16 | 11,912.31 | 27,239.68 | 27,998.11 |
| 같은 대화의 분석 비교 | 569.47 | 6,816.89 | 16,663.71 | 17,300.61 |
| 근거 부족 질문 / Basic | 476.12 | 5,397.04 | 12,289.66 | 12,810.93 |
| 근거 부족 질문 / 초기 Extended | 359.75 | 11,403.79 | 18,672.50 | 19,080.25 |
| 같은 질문 / 수정 후 Extended | 1,327.95 | 8,468.64 | 15,319.99 | 16,758.48 |
| 외부 문헌 이관 후 분석 | 542.54 | 12,835.14 | 24,389.73 | 24,981.32 |

기록은 각각 [wiki-initial](verification/live/wiki-initial.json), [analysis-comparison](verification/live/analysis-comparison.json), [gap-basic](verification/live/gap-basic.json), [gap-extended](verification/live/gap-extended.json), [gap-extended-fixed](verification/live/gap-extended-fixed.json), [research-answer](verification/live/research-answer.json)에 있다. 클라이언트에서 관측한 첫 텍스트 시점도 각 파일의 `stream.firstTextObservedMs`에 따로 보존했다. 서로 다른 경계에서 측정한 시간을 동일한 지표로 합산하지 않는다.

## 2. 하나의 대화에서 위키 → 분석 → 개인 위키

`conv_5626b07bd71b460b87be06d1a04197c6`에서 다음 흐름을 실행했다.

1. **위키 답변:** TSV–HBM 관계, 패키징 목적·원리, 적층 조건·한계, 삼성/SK 문헌의 범위를 질문했다. `핵심 설명 → 목적·원리 → 사례·조건 → 관계 → 출처·부족한 부분`의 순서로 실제 답변이 완료됐다. `run_03014fdd1ce1477a83c60a3e1229f922`에 저장됐다.
2. **분석 답변:** 같은 대화에서 TSV·와이어 본딩·플립칩의 연결 대상과 경로를 비교했다. 비교표와 문헌별 범위, 모든 패키지에서 서로 대체 가능하다고 결론 낼 수 없는 이유를 답했다. `run_cc0e35d48d4d40ce8508541a3517aea2`에 저장됐다.
3. **개인 위키 v1 추가:** 첫 답변 이후 개인 위키 작업 `job_6fed5f8f4b7646fdaba5eac1d32c71ac`가 `action=add`, `status=succeeded`, `version=1`로 완료됐다.
4. **동일 페이지 v2 병합:** 분석 답변 이후 `job_cb840e1044514a5282bf6b6ccdd05512`가 `action=merge`, `status=succeeded`, `version=2`로 완료됐다. 두 작업은 각각 한 번의 시도로 끝났고 동일 페이지 `pw_8a39721d668341f0b48e0f768d08bc09`를 가리킨다.

개인 위키 v2 제목은 **TSV·와이어 본딩·플립칩: 연결 경로와 적용 범위**다. 두 원메시지의 연결, 원문 구간 3개, 조건·한계, AI 생성 판본 이력이 남았다. 개인 위키 자체나 다른 AI 요약을 독립 근거로 인용하지 않았다.

개인 위키 작업·판본·사용량은 [personal-wiki-jobs.json](verification/live/personal-wiki-jobs.json)에 기록했다. 페이지 본문 대조에는 작업공간의 `wiki-page.json`을 사용했고 공개 문서에는 개인 페이지 전체 본문을 복제하지 않는다. [의미 검토 7절](verification/live/semantic-review.md)에 보존된 핵심 내용과 생략된 정보를 기록했다. 작업이 `succeeded`라는 사실은 병합이 완료됐다는 뜻이며, 모든 이전 지식이 손실 없이 보존됐다는 뜻은 아니다.

## 3. 외부 문헌 확보 → 대화 이관 → 실제 답변

### 확보와 이관

Lam Research의 공개 [Technical Glossary](https://www.lamresearch.com/technical-glossary/)에 대해 실제 research API를 호출했다. 환경의 기본 시스템 DNS 경로는 실패했으므로 검증 환경에서만 `google_doh_egress`를 명시적으로 선택했다. 공식 DoH로 조회한 주소의 공개 IP 여부를 확인하고, 검증한 IP로 연결하면서 원래 Host/SNI와 인증서 검증을 유지했다. 제품 기본값은 `system`이며 실패 시 검증을 생략하는 fallback은 없다. 경로와 보안 회귀는 [NETWORK.md](NETWORK.md)에 설명한다.

수정 후 [research-roundtrip.json](verification/live/research-roundtrip.json)의 실제 결과는 다음과 같다.

| 항목 | 관측 결과 |
|---|---|
| Fetch HTTP 상태 | 200 |
| Fetch 전체 관측 시간 | 12,752.15 ms |
| 확보한 추출 텍스트 | 30,371자 |
| 읽기 범위 | `partial` |
| 관련성 설명 | `relevanceStatus=generated` |
| 적용 한계 | 완전한 문장 5개로 저장 |
| 대화 이관 HTTP 상태 | 200 |
| 이관 결과 | 대화 첨부 1개와 공용 검토 후보 문헌 1개, 경고 없음 |

이관은 질문·조건을 반환하고 첨부 ID를 제공했다. `automaticPublicSubmissionIsAssumption=true`도 기록돼 있다. 생성된 공용 후보가 승인되거나 공용 검색에 공개됐다는 뜻은 아니다. 선택한 자료는 해당 소유자의 대화 첨부로 활용했다.

### 실제 결함과 재검증

[research-initial.json](verification/live/research-initial.json)에서는 fetch와 이관이 각각 200으로 성공했지만, 모델의 단일 문자열 `limitations`를 글자 단위로 잘라 저장한 결함이 있었다. 성공 HTTP 상태만 보고 문헌 카드 전체가 정상이라고 처리하지 않았다.

수정 후 응답 계약에 `relevance: string|null`, `limitations: list[string]`을 명시하고, 명백한 단일 문장은 한 항목으로 정규화한다. 잘못된 형식은 설명 생성 실패로 남기되 이미 확보한 본문과 관측 사용량은 보존한다. 후속 실제 결과에는 한 글자씩 분해된 한계 문구가 없고, 부분 발췌·제품 조건 부재·귀속 미검증을 설명하는 완전한 문장들이 있다. 기존 잘못된 레코드가 모두 소급 교정됐다고 주장하지 않는다.

### 원래 대화에서의 답변

[research-answer.json](verification/live/research-answer.json)은 위키와 분석을 수행한 원래 대화에서 첨부 `att_7b66284975ea462fb3a561073d316eae`를 사용했다. `run_ae8a3d833ac14b6388151d54a702ad7a`는 실제 스트림으로 완료됐다.

답변은 용어집의 2.5D·3D·TSV 설명을 앞선 SK 문헌과 연결하고, 부분 발췌의 한계를 밝혔다. 이 문헌으로 삼성/SK의 특정 제품 접합 조건이나 기술 우열을 판단할 수 없다고 제한했다. 이는 외부 자료가 대화 근거로 전달되어 실제 생성에 사용됐다는 확인이다. 해당 웹사이트 전체·영상·동적 내용·모든 도표를 확보했거나, 이 답변의 모든 기술적 추론을 전문가가 검증한 것은 아니다.

## 4. Extended에서 발견한 결함과 수정 후 결과

접합 온도·압력·허용 휨·양사 수율 차이를 묻는 동일 질문을 Basic과 Extended에 각각 새 대화로 실행했다. 두 초기 답변은 없는 수치를 만들어 내지 않았다. 그러나 초기 Extended의 탐색 상태는 잘못된 의미를 전달할 수 있었다.

| 관측 항목 | 초기 [gap-extended](verification/live/gap-extended.json) | 수정 후 [gap-extended-fixed](verification/live/gap-extended-fixed.json) |
|---|---|---|
| 탐색 계획 | `bounded_aspect_rules_v1` | `bounded_parameter_aspect_rules_v2` |
| 온도·압력의 구분 | 넓은 일반 조건 범주에 묶임 | 각각 `unknown` |
| 휨·수율 관련 근거 | 넓은 범주를 `evidence_found`로 표시 | 관련 언급을 `candidate_found`로 표시 |
| 내부 추가 검색 | 0회 | 1회 |
| 종료 이유 | `coverage_target_reached` | `no_new_evidence` |
| 의미 충분성 평가 | `not_evaluated` | `not_evaluated` |

초기에는 일반 키워드를 찾은 상태가 목표 충족으로 표시됐지만, 실제 질문의 수치 근거는 없었다. 후속 실행은 수치의 미확인 상태를 남기고 제한된 내부 검색 후 새 근거가 없다는 이유로 멈췄다. 외부 웹 조사를 자동으로 실행한 것은 아니다.

이는 **탐색 종료 상태의 개선을 실제 한 사례에서 확인한 것**이다. Extended의 정확도 향상률, 전체 예산 경계, 모든 반복·취소 상황을 증명하지 않는다. 일반 조건 후보에는 여전히 메타데이터 구간이 일부 포함되며, 의미 충분성을 자동 검증한 것으로 표시하지 않았다.

## 5. 새 스키마의 개념·관계 재추출

[ontology-fixed.json](verification/live/ontology-fixed.json)은 정책 `source-extract-v2-canonical-identity`로 같은 공개 문헌 3건에 대해 수행한 후속 실제 추출이다. `gpt-6-luna`를 **3회** 호출했으며, 각각 별도 문헌 작업으로 성공했다.

| 문헌 | 새 개념 | 기존 개념 재사용 | 출처별 설명 | 관계 |
|---|---:|---:|---:|---:|
| SK 미래인재 CLASS | 2 | 0 | 2 | 1 |
| 삼성 패키징 교육 | 7 | 0 | 7 | 7 |
| SK 하이피디아 TSV | 4 | 2 | 6 | 1 |
| 합계 | **13** | **2** | **15** | **9** |

마지막 문헌의 HBM과 와이어 본딩은 앞 문헌에서 만든 개념을 재사용하면서 각 문헌의 설명을 별도 source-view로 보존했다. `duplicateLabels=[]`, `alternativeRelationsWithoutConditions=[]`로 기록됐다. 초기의 조건 없는 TSV–와이어 본딩 대안 관계는 후속 결과에 없고, 와이어 본딩–플립칩의 대안에는 칩–기판 연결이라는 조건이 있다.

이 결과는 새 스키마의 추출·저장 확인이다. 파일에 `retrievalValidated=false`, `publicDataWrites=false`가 명시돼 있다. 기존 답변의 관계 카드가 소급 변경되거나, 새 관계를 통한 공통 RAG·후속 대화 전체가 추가로 검증됐다는 뜻은 아니다. 같은 라벨의 중복이 없다는 관측도 모든 별칭·동음이의어의 올바른 식별을 보장하지 않는다.

## 6. 브라우저에서 실제 스트림·새로고침·취소

[브라우저 실제 스트림 기록](verification/live/frontend-live-stream-result.json)은 `status=passed`, `errors=[]`, `generationPosts=1`이다. 프런트엔드에서 실제 Luna 답변을 받는 도중 다음 상태를 관측했다.

| 단계 | 저장/조회 상태 |
|---|---|
| 실행 시작 후 텍스트 수신 | `running`, `lastSeq=18`, 본문 2자 |
| 새로고침 후 같은 실행 복원 | `running`, `lastSeq=60`, 본문 84자 |
| 취소 후 최종 상태 | `cancelled`, `lastSeq=146`, 부분 본문 229자 |

실행 ID는 `run_2dc031286f0a4f709aa40b675520b5f7`이다. 새로고침 후에도 전송 전 입력 초안이 복원됐고, 취소된 부분 답변에 취소 상태가 남았다. 다시 불러와도 답변을 중복 생성하지 않았다. 기록된 POST는 로그인, 답변 생성 1회, 클라이언트 시간 기록 1회, 취소 1회다.

- 서버의 첫 실제 답변: **4,990.26 ms**.
- 브라우저의 첫 표시 관측: **5,107.80 ms**, `clientTimingSource=browser_untrusted`로 기록.
- 취소까지의 서버 전체 시간: **6,164.78 ms**.

usage 집계의 `calls=2`는 답변 생성 요청 두 번을 뜻하지 않는다. 실제 query embedding 1회와 생성 1회다. 취소된 생성에서는 공급자의 최종 usage가 도착하지 않아 토큰 합계와 총비용이 null/unknown으로 남았다. 부분 답변이 보였다는 이유로 미수신 사용량을 추정해 채우거나 비용 0으로 표시하지 않았다.

## 7. 사용량과 비용

금액과 호출 범위의 기준은 **[usage-ledger.json](verification/live/usage-ledger.json)**이다. 초기 개별 실행 파일의 잠정 비용 값보다, 미확인 항목을 다시 구분해 집계한 이 원장을 사용한다.

| 항목 | 이번 추가 라이브 검증의 집계 |
|---|---:|
| 전체 공급자 호출 | 25회 |
| `gpt-6-luna` 호출 | 17회 |
| `text-embedding-3-large` 호출 | 8회 |
| 실제 usage를 관측한 호출 | 24회 |
| 관측된 입력 토큰 합계 | 87,169 |
| 관측된 출력 토큰 합계 | 24,109 |
| 확인 가능한 추정 비용 `knownEstimatedCostUsd` | **USD 0.01980707** |
| 비용을 확정해 계산할 수 없는 호출 | **4회** |
| 전체 비용 `totalCostUsd` | **null** |
| 청구서 대조 | 수행하지 않음 (`invoiceVerified=false`) |

미확인 4회는 초기 온톨로지 생성 3회의 cache-write 수명 정보 누락과, 취소된 생성 1회의 최종 usage 미수신이다. 따라서 24회의 토큰 usage를 관측했더라도 24회 모두 비용을 산출할 수 있는 것은 아니다. 관측된 입력·출력 토큰도 미수신 호출을 포함한 전체 사용량으로 간주하지 않는다.

이 원장은 이번 별도 라이브 DB 및 새 스키마 검증만 포함한다. 이전 임베딩 비교 실험, 앞선 353토큰 API smoke, metadata·웹 fetch는 제외한다. 알려진 추정액은 전체 청구액이나 예산 상한이 아니며, 미확인 비용을 0으로 더한 합계도 아니다.

## 8. 자동 테스트·브라우저·Compose의 상태 구분

| 검증 종류 | 이 문서 작성 시점의 상태 | 해석 |
|---|---|---|
| 백엔드 회귀 | [backend-tests.xml](verification/backend-tests.xml): **200개 통과**, 실패·오류·건너뜀 0 | 격리 PostgreSQL 스키마의 계약·권한·상태·회귀 검증. 실제 모델의 의미 품질 점수가 아니다. |
| 실제 Luna 브라우저 스트림·복원·취소 | 위 6절의 실행 성공 | 공개 문헌 3건으로 제한한 한 실제 생성의 브라우저 확인. |
| 프런트엔드 최종 회귀·빌드 | **7개 파일·28개 테스트 통과**, TypeScript/Vite build 성공, 최종 GET 브라우저 검증 통과 | [frontend-verification.md](verification/live/frontend-verification.md). 취소 검증 후 스크롤 수정은 DOM 회귀와 저장된 실제 부분 답변의 GET 복원으로 확인했으며 유료 스트림을 다시 실행하지 않았다. |
| Docker Compose | 로컬 Docker runtime 부재. GitHub Actions smoke 작성, push 후 실행 결과 확인 예정 | YAML·보호 검사·스크립트 작성과 실제 Compose 기동을 구분한다. [COMPOSE_SMOKE.md](COMPOSE_SMOKE.md) 참조. |
| 운영 이전·배포 | 미수행 | 운영 DB·운영 부하·전환·롤백 실증을 완료했다고 주장하지 않는다. |

fixture 모드는 네트워크 모델 호출 없이 계약과 실패 처리를 확인하는 별도 경로다. 이 문서의 actual/live 기록과 합쳐서 호출 성공 횟수나 모델 응답 품질을 계산하지 않는다. 특히 fixture의 구조화 생성 실패를 실제 개인 위키·관계 생성 성공으로 간주하지 않는다.

## 9. 남은 의미 품질의 한계

원문을 대조한 [semantic-review.md](verification/live/semantic-review.md)에 다음 제한을 남겼다.

1. **조건의 인과 압축:** Extended 답변은 적층 높이에 따른 휨과 밀집 구조의 발열을 하나의 높이 증가 인과로 묶는 표현이 있다. 정량 환각은 아니지만 원문의 조건 구분보다 거칠다.
2. **발언 귀속과 시점:** HBM source-view의 “수백 배”는 원문에 있는 교수의 소개 발언이지만, 요약에는 발언자·제품 세대·측정 조건이 충분히 남지 않았다. 삼성 자료 본문의 2018년 게시일도 인용 메타데이터에서는 null이다. 이를 최신 기업 공식 성능 사양으로 사용해서는 안 된다.
3. **개인 위키의 압축 손실:** v2는 핵심 비교와 제한을 유지하지만, HBM의 수직 적층 D램 정의·미래인재 CLASS 설명 범위·보호 환경 예시가 줄었다. 이번 snapshot에는 v1 전체 본문이 없어 모든 편집 차이를 복원한 검토가 아니다.
4. **출처 연결과 의미 검증의 차이:** 본문 인용은 원문 구간으로 추적되지만, 그것만으로 모든 관계·비교·요약이 정확하다는 결론은 낼 수 없다. 승인된 문헌의 자동 추출 결과는 문헌 승인과 별개로 추출 상태를 유지한다.
5. **평가 범위:** 공개 문헌 3건과 외부 용어집 한 건의 소수 흐름이다. 문헌 전체의 검색 누락, 장기 개인 위키 병합, 전문가가 정의한 정답·허용 추론 범위, 운영 부하·장애·모든 예산 경계는 이 실제 호출 집합으로 검증되지 않았다.

초기 결함·수정 후 결과·미확인 상태를 함께 남겼다. 후속 구현자는 실행 ID와 원문 판본을 기준으로 어떤 단계에서 문제가 생겼고 무엇을 다시 검증했는지 추적할 수 있다.
