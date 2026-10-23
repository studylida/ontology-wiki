# 온톨로지 위키 메인 DB 전환·통합·HTTP E2E 및 AI 비용 측정

기록 시각: 2026-10-23T13:18:37+09:00. 로컬 Windows 환경의 실제 실행 결과이며 운영 배포·전체 의미 정확도 인증이 아니다.

## 현재 상태

- 서비스: http://127.0.0.1:3000/ . 백엔드·정적 빌드: http://127.0.0.1:8000/ . 새 서버의 healthz, 프론트 프록시, 정적 화면 모두 HTTP 200이다.
- 메인 DB: `C:/Users/BISTelligence/ontology-wiki/data/ontology_wiki_v2.db`.
- 원본: `.work/scale-review/wiki-seed-v5.sqlite3`. 129문헌의 오프라인 원문 검토 시드이며 API로 129건을 다시 추출한 데이터가 아니다. 개념 494, 사례 215, 관계 339, 근거 1,614, 문헌 129건이다. 124문헌 적용, 기술 내용 없는 5문헌은 빈 결과를 유지한 정본이다.
- 최종 SQLite integrity는 ok, 외래 키 오류는 0이다. 메인의 개념·사례·관계·근거·문헌 테이블 전체 행 서명이 정본 백업과 같다. 원문 129개 파일 해시도 모두 같다.
- 메인의 검토 티켓·감사·비교·조사 이력은 각각 0건이다. 기존 메인의 이력은 이전 DB 백업에 보존했으며 새 시드 DB에 이관하지 않았다. 검증용 계정·발의·저장·재추출·적용은 별도 사본에서만 수행했다.

## 백업과 복원

백업 폴더: `C:\Users\BISTelligence\ontology-wiki\data\backups\20261023T034333Z`.

| 파일 | 용도 | SHA-256 |
|---|---|---|
| seed-v5-canonical.sqlite3 | 재사용할 깨끗한 최종 시드 | `0d583425e70aea7af8a2bab35b40104d4ba0ed3553a1ccd289a3f32931841461` |
| previous-main-stopped.sqlite3 | 서버 정지 후 기존 메인 전체 백업 | `6e348e11a10d6b9221d82c313513af0efcadfae468b0ba3134292890e8dbba70` |
| previous-main-online.sqlite3 | 전환 전 SQLite backup API로 만든 추가 백업 | `6e348e11a10d6b9221d82c313513af0efcadfae468b0ba3134292890e8dbba70` |

[backup-manifest.json](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/backup-manifest.json)에 원본 경로·원본 해시·백업 해시·전환 경로를 보관했다. 원본 v5 파일도 바꾸지 않았다. 기존 DB에서 관찰한 외래 키 오류 2건은 과거 상태 그대로 백업했으며 임의 보정하지 않았다.

복원 시에는 8000번 제품 백엔드를 먼저 종료하고, 현재 메인을 SQLite backup API로 새 경로에 보관한 뒤 원하는 백업을 `data/ontology_wiki_v2.db`로 복원한다. 활성 SQLite 연결과 WAL/SHM/저널이 있는 상태에서 파일을 덮지 않는다. 새 파일 무결성·외래 키·행 수를 확인하고 서버를 시작한다. 백업 원본을 직접 서비스 DB로 열어 쓰지 않는다. 재생성 절차는 `backend/seeds/offline_sources_20261023/README.md`에 있다.

## 이번에 실제 반영한 코드

1. 탭4 최종 구현 `f2b0e07`과 그 선행 조사 구현이 별도 체크아웃에만 있음을 발견했다. `tab4-before`의 제품 사본, 현재 제품, 최종 구현을 대조해 조사 소유 파일 25개만 통합했다. 검토 전체 편집 관련 파일은 복사하지 않았다. 비교 Service는 공개 사양·복수 근거 수정을 보존한 3방향 병합으로 조사 근거 사용 부분만 합쳤고, 조사 Service의 이후 규모 분류 안내 정정도 보존했다. `pypdf==6.21.2`를 기존 venv에 설치했다. [integration-applied.json](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/integration-applied.json)에 파일·사전/사후 해시가 있다.
2. 일반 첫 접속이 예전 고정 ID `concept-tcb`를 조회해 404가 나는 실제 문제를 수정했다. App은 URL의 명시적 개념만 전달하고, 지정이 없으면 기존 Wiki Controller가 서버 트리의 첫 등록 개념을 연다. 새 고정 ID나 DB 보정은 넣지 않았다. 먼저 명시적으로 선택한 개념을 초기 트리 응답으로 대체하지 않는다. 일반 첫 접속·명시적 IC 주소의 실제 브라우저 결과와 기존 선택 회귀를 확인했다.
3. 올바른 `frontend` 폴더에서 Vite 빌드를 수행하고 백엔드와 3000번 개발 서버를 다시 시작했다. `.env`와 키·모델 설정 파일은 수정하지 않았다. 메인 백엔드는 프로세스의 `DEBUG=false`로 SQL 바인딩 디버그 기록을 끄고 실행한다. 최초 진단 로그의 드라이버 디버그 행도 표시하지 않고 제거했다. 인증 응답·토큰·키·프롬프트를 측정 자료에 저장하지 않는다.

공유 브랜치 `fix/wiki-knowledge-flow`, HEAD `fa2d74b020db257934a10f4416d3a246c8f017bf`, 공유 index를 유지한다. 자신의 변경은 별도 index와 로컬 ref로 기록하며 기존 변경을 reset/clean/stash/전체 파일 복사로 되돌리지 않는다. 원격 push·배포는 하지 않았다. 이번 적용은 현재 로컬 작업본의 실행 전환이다.

## 검증 경계와 방법

메인에는 공개 GET·브라우저 진입 확인만 수행했다. 쓰기·실제 AI 검증은 새 시드 사본 `qa.sqlite3`, 별도 loopback 포트, 실제 FastAPI 앱·라우터·Service·Repository·DTO와 기존 모델 설정을 사용했다. 테스트 역할 2/3/4 계정은 이 사본에만 추가했다. httpx로 실제 TCP HTTP를 호출했고, 모델과 Crossref 응답을 모의하지 않았다. QA 프로세스 안에서 HTTP 응답의 usage·model·시간만 관찰하는 래퍼를 붙였으며 응답·프롬프트·Gateway 반환·판정·저장 동작을 바꾸지 않았다. 평상시 메인 서버의 상시 과금 수집 기능을 추가한 것은 아니다.

화면은 새 headless Chrome 156.0.8078.47, 1680×1050에서 실제 빌드와 로그인 API로 발급한 테스트 토큰의 세션 복원을 사용했다. 사용자 브라우저는 조작하지 않았다. 브라우저 API 오류·pageerror는 0건이고 7개 화면의 실제 캡처를 보관했다. 모든 입력 폼을 실제 모델과 조합해 자동 조작한 것은 아니며 화면 진입 검사와 HTTP 기능 검사를 구분한다.

Python 3.11.9, FastAPI 0.146.0, Pydantic 2.14.1, SQLAlchemy 2.1.5, httpx 0.28.1, uvicorn 0.54.0, pypdf 6.21.2, Vite 5.4.21 환경이다. SQLite·인메모리 QA 캐시이며 PostgreSQL·다른 OS·다른 브라우저·부하/SLA는 확인하지 않았다. 측정에는 로컬 실행·계측·네트워크 지연이 포함된다. 최초 QA 실행의 드라이버 DEBUG 출력은 측정에 부하를 더했으며 기록에서 제거했다. 재실행 스크립트는 DEBUG=false를 명시한다.

## View·Controller별 결과

| View / Controller | 실제 HTTP 흐름 | 결과 |
|---|---|---|
| 대시보드 / useDashboardController | health·version·역할3 감사 검증 | 통과. 개념494·근거1614. 감사가 없는 초기 DB 검증이므로 승인 후 전체 운영 체인 검증과 구분한다. |
| 위키 / useWikiController | 4패싯·5규모 트리, 상세494건, 2-hop, 문맥 설명, 편입 추천, 사례 해설 캐시·권한 | 통과. 명시적 IC는 Scale2. 선택 문자열·공백·역방향·1px 더블클릭·113px 복귀 드래그 회귀도 통과했다. |
| 검색 / useTopBarController | 기존 spotlight API·검색 모달·HBM 입력 | 통과. 고정 개념 ID 없이 실제 등록 결과를 사용한다. |
| 비교 / useComparisonController | 등록 대상 조회→비교 생성→매트릭스→꼬리질문→공정 상담→티켓 발의 | 통과. 실제 등록된 `mr-muf`와 `tcb`를 사용했고 매트릭스 8행이다. 최초 검사에서 TC-NCF ID가 있다고 가정한 입력 오류는 원본 실패 기록을 보존하고 실제 등록 대상의 후속 검사로 정정했다. |
| 검토 / useReviewController | 생성·큐·상세·잠금→개요·목적·원리 저장→구판본409→지시문→미리보기 | 통과. 직접 수정한 개요·목적은 AI 보강 후에도 같다. 최종 QA 티켓 2건은 모두 pending, 감사0건으로 승인하지 않았다. 전체6목차·승인·동시성·L3는 별도 기존 제어응답 격리 회귀도 통과했다. |
| 조사 / useResearchController | 실제 질문 해석→Crossref/등록자료 탐색→같은 세션 재개·복원 | 실행 통과, 유용한 결과 확보는 미완료. 후보 66→113건, 이전 ID 보존. 포함0건이므로 종합 분석·조사 후보 발의·비교 보강은 실제 모델 흐름에서 진행하지 않았다. |
| 관리자 / useAdminController | 권한401/403·129문헌 목록·상태·잘못된ID400→식각 재추출 SSE 연결 해제→완료→미리보기→적용 | QA에서 통과. 팝업 연결을 끊은 뒤 약58.39초에 완료했고 1문서·기존 개념9개에 적용했다. 메인에는 적용하지 않았다. 적용 후 비동기 해설 생성6회도 비용에 포함했다. |

기본 실행은 67개 단언 중65개가 통과하고2개가 남았다. 하나는 존재하지 않는 TC-NCF ID를 가정한 검사 입력 오류로 후속 비교 HTTP 5개가 통과했다. 다른 하나는 포함 문헌이 없다는 종합 분석 전제조건 미충족으로 그대로 남긴다. 후속 비교·QA 적용 HTTP6개와 저장 응답 계약11개도 모두 통과했다. 이 숫자들을 합쳐 전체 서비스 E2E가 완전 통과했다고 표현하지 않는다. [qa-summary.json](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/qa-summary.json), [contract-checks.json](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/contract-checks.json), [browser-extra-api.json](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/browser-extra-api.json), [browser-results.json](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/browser-results.json) 참조.

## 실제 AI 시간·토큰·비용

아래 토큰은 문자 수 추정이 아니라 실제 provider 응답 usage다. 시간은 API 왕복 초이며 비동기 적용 해설은 제공자 호출의 합계와 구분한다. 출력에는 응답이 제공한 reasoning/thinking 사용량을 포함하고 별도 중복 합산하지 않는다. 호출 횟수에는 응답 미관측 시도도 포함한다. 비용은 사용량이 확인된 부분만 계산한 표준 유료 요금 추정치다.

| 기능 | 요청 모델 | API 초 | 호출 | 확인된 입력 / 출력 토큰 | 확인분 추정 USD | usage 미확인 호출 |
|---|---|---:|---:|---:|---:|---:|
| 챗 Local | gpt-4o-mini | 5.40 | 1 | 5,962 / 355 | $0.001107 | 0 |
| 챗 Global | gpt-4o | 2.62 | 1 | 345 / 146 | $0.002322 | 0 |
| 선택 용어 설명 | gpt-4o-mini | 1.60 | 1 | 134 / 53 | $0.000052 | 0 |
| 편입 위치 추천 | gpt-4o-mini | 2.71 | 1 | 22,883 / 125 | $0.003507 | 0 |
| 검토 지시문 보강 | gpt-4o | 6.56 | 2 | 52,024 / 324 | $0.133300 | 0 |
| 조사 질문 해석 | gpt-6.1-sol | 12.57 | 1 | 572 / 452 | $0.005664 | 0 |
| 최초 문헌 조사 | gpt-6.1-sol | 150.07 | 8 | 8,026 / 5,453 | $0.070582 | 3 |
| 이어서 조사 | gpt-6.1-sol | 150.08 | 7 | 6,363 / 4,469 | $0.054180 | 3 |
| 식각 문서 재추출 | gemini-3.8-flash | 58.39 | 5 | 63,577 / 6,880 | $0.071772 | 0 |
| 추출 적용 후 해설 생성 | gpt-4o-mini | 0.92 | 6 | 6,049 / 1,123 | $0.001581 | 0 |
| 비교 생성 | gpt-4o | 5.42 | 1 | 3,302 / 656 | $0.014815 | 0 |
| 비교 꼬리질문 | gpt-4o | 5.91 | 1 | 3,328 / 707 | $0.015390 | 0 |
| 공정 조건 상담 | gpt-4o | 4.33 | 1 | 4,150 / 593 | $0.016305 | 0 |

적용 API의 0.92초는 응답 반환까지의 시간이며, 이어지는 해설 생성6회의 제공자 시간 합은18.20초다. 추출 완료 58.39초와 제공자 호출 합56.26초도 구분한다.

총 제공자 시도 **36회**, usage 확인 **30회**, 미관측 **6회**다. 확인된 사용량의 추정액은 **$0.390578**다. 미관측 호출은 시간 제한/연결 종료로 응답을 받지 못한 시도이며 0원으로 처리하지 않는다. 최종 청구액·무료 구간·회사 계약 할인·환율·세금은 확인하지 않았다. 요청 모델과 실제 반환 모델·캐시·추론 토큰·HTTP 상태·호출별 시간은 [llm-measurements.csv](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/llm-measurements.csv)와 [llm-metrics.jsonl](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/llm-metrics.jsonl)에 구분했다. 메인 서버의 이후 사용자 호출 비용은 이 수치에 포함하지 않는다.

2026-10-23 공개 Standard 단가(백만 토큰당 입력/캐시입력/출력 USD)는 GPT-4o-mini 0.15/0.075/0.60, GPT-4o 2.50/1.25/10, GPT-6.1 Sol 2/0.10/10, Gemini3.8 Flash 0.75/0.075/3.75를 사용했다. `((입력-캐시)×입력단가 + 캐시×캐시단가 + 출력×출력단가)/1,000,000`으로 계산했다. 요금은 시점·서비스 등급에 따라 바뀔 수 있다. [OpenAI GPT-4o](https://developers.openai.com/api/docs/models/gpt-4o), [GPT-4o-mini](https://developers.openai.com/api/docs/models/gpt-4o-mini), [GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol), [Gemini 공식 요금](https://ai.google.dev/gemini-api/docs/pricing). [cost-summary.json](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/cost-summary.json)에 단가 기준일과 출처를 보관했다.

시드129건은 오프라인 검토 산출물이므로 이번 식각1건의 58초/$0.071772를 129건 전체의 실측 비용으로 말하면 안 된다. 이번 조사와 추출 표본은 기능별 한 번의 실행이며 모델 평균 속도·정확도·비용 보장은 아니다. 지시문 보강은 두 호출에서 입력52,024토큰을 사용해 약$0.1333였고, 모델 이름뿐 아니라 전달하는 위키·문헌 문맥의 크기도 비용에 영향을 준다.

## 남은 사항과 회사 설명 시 구분

- 이번 HBM 조사는 후보113건 중 포함0·제외22·보류91건이다. 보류 사유는 내용부족2·평가실패4·평가대기85다. 첫 조사와 재개는 각각150초 예산을 사용했다. 이 실행으로 관련 논문이 없다고 결론 내리지 않는다. 검색·원문 접근·판정의 유효 결과 확보가 남은 품질 한계이며, 종합 분석 이후 경로의 실제 모델 성공을 주장하지 않는다. 일부 AI 잔여 질문에는 중국어가 섞여 언어 일관성도 남았다.
- 새 조사 계약과 기존 `verify_research_flow.py`의 무평가 fixture/검토 `/wikiDraft` 기대값 차이는 기존 실패 기록에 남아 있다. 이번 작업에서 검사 기대값이나 검토 서비스를 바꿔 통과시키지 않았다. 새 discovery·continuation 회귀와 기존 whole-editor·directive 회귀는 실제 현재 코드에서 통과했다.
- 승인 버튼은 UI에 표시되지만 실제 모델을 사용하는 이번 HTTP 검증에서 승인·반려하지 않았다. 승인 성공·충돌·L3의 격리 제어응답 회귀 통과와 실제 모델 승인을 구분한다. 기존 시드의 사례는 공개 사례이며 비공개 실제 회사 데이터로 검증하지 않았다.
- 검토 화면 일부 목적 문장에서 원문의 `\mu m` 같은 수식 표기가 그대로 보인다. 값 손실이나 저장 오류가 아니라 남은 표시 정리 사항으로 관찰했으며 이번 실행 전환에서 임의로 원문·수치를 고치지 않았다.
- 지속적인 운영 비용 집계·청구 API 연동은 미구현이다. 이번에는 검증 프로세스에서만 관측했고 반복·동시 사용·운영 PostgreSQL·장시간 부하·다른 브라우저는 미확인이다. 빌드는 통과했으며 기존 큰 번들 경고는 남겼다.

## 재현 자료

- [qa_run.py](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/qa_run.py): 별도 seed 사본·서버·역할별 실제 HTTP·provider metadata 관측. 기존 QA DB가 있으면 덮지 않고 중단한다. 다른 결과 폴더에서 실행해야 한다. 실제 AI와 외부 검색 비용이 발생한다.
- [qa_browser.mjs](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/qa_browser.mjs): 실제 빌드·인증 복원·등록 비교 대상·7개 화면. 인증값은 실행 중 stdin으로만 전달하며 파일에 저장하지 않는다.
- [api-results.jsonl](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/api-results.jsonl), [qa-summary.json](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/qa-summary.json), [contract-checks.json](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/contract-checks.json): 요청별 상태·시간, 성공과 전제조건 미충족을 구분한다.
- [main-browser-smoke.json](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/main-browser-smoke.json), [main-browser-after.json](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/main-browser-after.json): 첫 접속의 고정ID 오류와 수정 후 결과.
- [main-preservation.json](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/main-preservation.json), [final-health.json](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/final-health.json): 메인 지식 불변·최종 서비스 확인.
- [verify_research_discovery.py.log](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/verify_research_discovery.py.log), [verify_research_continuation.py.log](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/verify_research_continuation.py.log), [verify_review_full_editor.py.log](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/verify_review_full_editor.py.log), [verify_review_directive.py.log](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/verify_review_directive.py.log), [wiki-selection.log](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/wiki-selection.log): 모의 외부 응답 또는 격리 브라우저 회귀. 실제 provider 측정과 구분한다.
- 화면: [view-wiki.png](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/view-wiki.png), [view-dashboard.png](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/view-dashboard.png), [view-comparison.png](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/view-comparison.png), [view-review.png](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/view-review.png), [view-research.png](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/view-research.png), [view-admin.png](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/view-admin.png), [view-search.png](C:/Users/BISTelligence/.codex/.chatgpt-projects/g-p-6a463aaf86688191953a9a41b12a7fa0/.work/main-service-20261023/view-search.png).

로컬 커밋·최종 상태는 같은 작업 폴더의 `commit.json`과 `source-final.json`에 기록한다. 기존 다른 세션 변경은 공유 작업본에 남아 있다.
