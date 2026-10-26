# 격리 Compose smoke 검증

`.github/workflows/compose-smoke.yml`은 개발용 `compose.dev.yml`을 실제 Docker 환경에서 검증합니다. `feat/conversation-rag-redesign-20261026` 브랜치의 코드 push와 `workflow_dispatch`에 연결했으며, 표준 `ubuntu-latest` 러너 한 개와 최대 15분을 사용합니다. `docs/**`와 `README.md`만 바뀌는 기록 갱신은 새 실행을 만들지 않습니다. GitHub 토큰 권한은 `contents: read`이고 checkout 자격증명을 지속 저장하지 않습니다. 배포·이미지 게시·저장소 push는 수행하지 않습니다.

**2026-10-26 GitHub Actions의 실제 Compose 실행이 통과했습니다.** 이 로컬 환경에는 Docker CLI·daemon이 없어 컨테이너 검증은 GitHub의 별도 Ubuntu 러너에서 수행했습니다. [실행 40274989231](https://github.com/studylida/ontology-wiki/actions/runs/40274989231)의 검증 코드 커밋은 `cab8519953136d89df9d7a19379b9c576b3b0662`이며 최종 상태는 `completed/success`입니다. 컨테이너·볼륨 정리를 포함한 여섯 단계가 모두 성공했습니다. 상세 집계는 [compose-ci.json](verification/compose-ci.json)에 있습니다.

실제 PostgreSQL 16.15/pgvector 0.8.7, web/API 연결, 문헌 승인·색인, SSE 13개 이벤트, 같은 요청의 멱등성, API 컨테이너 재시작 후 대화·SSE 복원을 확인했습니다. 이 실행은 fixture 전용이고 외부 모델 호출은 0회입니다. 실제 GPT-6 Luna의 별도 검증은 [LIVE_VERIFICATION.md](LIVE_VERIFICATION.md)를 참고합니다.

첫 [실행 40274683723](https://github.com/studylida/ontology-wiki/actions/runs/40274683723)은 이미지 빌드·DB 초기화 뒤 시작 준비 GET의 `ConnectionResetError`를 처리하지 못해 실패했습니다. API 60초·web 30초의 준비 GET만 제한적으로 재시도하도록 수정했고, 정상 조건·제한시간·POST 무재시도를 확인하는 회귀 5개를 추가한 후 위 새 실행에서 전체 흐름을 통과했습니다. 초기 실패는 성공으로 덮지 않고 기록에 남겼습니다.

## 실제로 확인하는 흐름

`scripts/v2/compose_smoke.py`는 다음을 순서대로 실행합니다.

1. 사용할 Docker endpoint가 명시적인 로컬 Unix socket인지 확인합니다. 임의의 remote Docker context를 사용하지 않습니다.
2. 이번 실행 전용 `ow-ci-<무작위 값>` project와 임시 loopback 포트 세 개를 정합니다. DB 비밀번호·인증 서명 secret·검토자 비밀번호를 새로 만들고 mode 0600의 임시 상태 파일에만 기록합니다.
3. 기존 앱 `.env`나 Docker 인증 설정을 읽지 않고, 명시적으로 `provider=fixture`, 빈 모델 API 키, 별도 Docker config 디렉터리를 사용합니다. 부모 프로세스의 공급자·GitHub 자격증명을 Compose에 전달하지 않습니다.
4. Compose config 검사, 이미지 build, PostgreSQL+pgvector 기동, 새 개발 스키마 마이그레이션, 검토자 계정 생성, API·worker·web 기동을 실행합니다.
5. DB 연결·fixture 모드·pgvector extension, web HTML과 web→API proxy 경로를 확인합니다.
6. 로그인하고 합성 문헌을 등록합니다. 승인과 검색 반영 상태가 구분되는지 확인한 뒤 즉시 색인 작업과 원문 판본/구간 조회를 확인합니다.
7. 기본 위키·Extended off 대화에서 질문을 제출하고 실제 HTTP SSE의 시작·검색·본문 delta·인용·완료 이벤트를 읽습니다. 수신 delta와 저장된 본문·출처 판본을 비교합니다.
8. 같은 `clientRequestId`를 다시 제출하여 새 실행이 만들어지지 않는지 확인합니다.
9. API 컨테이너를 재시작한 뒤 같은 대화·메시지를 복원하고 영속 SSE 이벤트를 다시 읽어 비교합니다.
10. 정리용 JSON을 제공하지 않는 기본 fixture 때문에 발생한 온톨로지 추출·개인 위키 작업의 실제 `failed / structured_output_invalid` 상태를 확인합니다. 가짜 개인 위키 페이지가 생성되지 않고 공급자 호출 수가 0인지 확인합니다.

마지막 항목은 구조화 생성 성공을 뜻하지 않습니다. Compose의 작업 실행과 실패 상태 보존을 확인하는 항목이며, 구조화 생성·의미 품질의 실제 모델 검증과 구분합니다. 성공 결과에도 `structuredGenerationSuccessVerified=false`, `semanticQualityEvaluated=false`를 기록합니다.

## 정리 범위와 결과

워크플로의 `always()` 단계는 해당 실행에서 생성한 project에만 `docker compose down --volumes --remove-orphans`를 적용합니다. 기존 개발/운영 project, 기존 DB, 다른 볼륨을 찾거나 삭제하지 않습니다. `docker system prune`이나 전역 볼륨 정리는 하지 않습니다. API·worker·web의 기존 기본 포트는 유지하며, CI만 `OW_DEV_DB_PORT`, `OW_DEV_API_PORT`, `OW_DEV_WEB_PORT`로 별도 포트를 지정합니다.

검증 결과는 실행 로그와 GitHub job summary, 러너 임시 디렉터리의 `result.json`에 남깁니다. 비밀번호·서명 secret·bearer token은 출력 전에 가리고, 임시 `.env`와 상태 파일을 artifact로 올리지 않습니다. cleanup은 생성한 비밀 파일도 지웁니다. 실패는 0이 아닌 종료 코드와 실패 단계로 남으며 성공 결과로 재해석하지 않습니다.

일반 Docker 개발 환경에서 수동 실행하려면 저장소 루트에서 다음을 사용합니다.

```bash
python3 scripts/v2/compose_smoke.py run --state-dir /tmp/ontology-compose-smoke
python3 scripts/v2/compose_smoke.py cleanup --state-dir /tmp/ontology-compose-smoke
```

`run`이 실패해도 `cleanup`을 실행합니다. 기본 socket은 `unix:///var/run/docker.sock`이며, 다른 로컬 socket은 `--docker-host unix:///실제/로컬/socket`으로 지정합니다. TCP·SSH 등 remote daemon은 거절합니다. 같은 state 디렉터리에 미정리된 실행이 있으면 덮어쓰지 않습니다.

## Actions 비용 조건

[GitHub의 공식 Actions 과금 안내](https://docs.github.com/en/billing/managing-billing-for-github-actions/about-billing-for-github-actions)는 공개 저장소의 표준 GitHub-hosted runner 사용을 무료 대상으로 설명합니다. 이 워크플로는 그 조건에 맞는 표준 Ubuntu 러너를 요청하고 larger runner·유료 외부 모델·artifact/cache 업로드를 사용하지 않습니다. 저장소 공개 범위·실제 runner 종류·계정 정책은 실행 시에도 확인해야 하며, 이 설명을 계정 청구서 확인으로 표현하지 않습니다.

checkout은 확인한 공식 `actions/checkout` v6.0.3 릴리스를 지정했습니다. [공식 릴리스 목록](https://github.com/actions/checkout/releases)을 기준으로 버전을 갱신하고, 변경 시 같은 Compose 실행을 다시 확인합니다.
