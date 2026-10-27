# Windows 로컬 실행

이 안내는 `C:\Users\BISTelligence\ontology-wiki-conversation`의 2026-10-26 로컬 개발 환경을 다시 실행하는 방법입니다. 구조와 데이터 책임은 [ARCHITECTURE.md](ARCHITECTURE.md), API와 인증 계약은 [API.md](API.md), 재시작과 작업 경계는 [backend-architecture.md](backend-architecture.md)를 따릅니다.

## 준비된 환경

이 환경은 Python 3.12.13, Node.js 24.19.0, portable conda-forge PostgreSQL 16.15와 pgvector 0.8.6을 사용합니다. 인계 기준 커밋은 `3cb72d5`입니다. 일반 설치 기준은 [README.md](../README.md)를 따르며, 설치 출처는 [Python](https://www.python.org/downloads/windows/), [Node.js](https://nodejs.org/en/download), [conda-forge PostgreSQL](https://anaconda.org/conda-forge/postgresql), [pgvector](https://github.com/pgvector/pgvector)입니다.

Python 실행파일은 `.venv\Scripts\python.exe`, Node.js는 `C:\Program Files\nodejs\node.exe`, Vite는 `frontend\node_modules\vite\bin\vite.js`입니다. DB 실행파일은 `var\pgsql\Library\bin`, 클러스터는 `var\pgdata`, DB 로그는 `var\postgres.log`입니다. 의존성, DB 클러스터와 마이그레이션, `my-reviewer` 계정, 서버용 `.env`가 이미 준비되어 있어야 합니다. 이 helper는 설치·마이그레이션·계정 생성·문헌 반입을 수행하지 않습니다.

계정 비밀번호는 로컬 전용 파일 `var\login.local.txt`에서 확인합니다. 키와 비밀번호, `.env` 내용은 채팅·화면 캡처·Git에 넣지 않습니다. helper도 `.env`나 키 파일의 내용을 읽거나 출력하지 않으며, 기존 `dev.py`가 서버 프로세스 안에서 `.env`를 불러옵니다.

## 시작·확인·종료

PowerShell 7에서 저장소 디렉터리로 이동한 뒤 실행합니다. 아래 명령은 실행 정책이나 신뢰 설정을 변경하지 않습니다.

```powershell
Set-Location 'C:\Users\BISTelligence\ontology-wiki-conversation'
pwsh -NoProfile -File .\scripts\v2\windows_dev.ps1 -Action start
pwsh -NoProfile -File .\scripts\v2\windows_dev.ps1 -Action status
```

화면은 [http://127.0.0.1:5173](http://127.0.0.1:5173), API 상태는 [health](http://127.0.0.1:8001/api/v1/health), API 명세는 [docs](http://127.0.0.1:8001/docs)입니다. `my-reviewer`로 로그인합니다. Vite의 API 프록시는 시작할 때 `http://127.0.0.1:8001`로 지정됩니다. DB는 `127.0.0.1:55432`를 사용하며 기존 `8000`·`5432` 서비스는 종료하거나 변경하지 않습니다.

시작하면 PostgreSQL, API 한 개, DB 작업자 한 개, Vite 한 개를 숨김 프로세스로 실행합니다. 터미널을 닫아도 실행이 이어집니다. 같은 helper를 다시 시작하면 기록된 실행파일·PID·생성시각을 확인하여 재사용합니다. API나 웹 포트를 기록되지 않은 다른 프로세스가 사용하면 시작을 중단합니다. worker의 실행 상태는 프로세스 생존을 뜻하며 대기 중 작업의 성공을 보장하지 않습니다.

```powershell
pwsh -NoProfile -File .\scripts\v2\windows_dev.ps1 -Action stop
pwsh -NoProfile -File .\scripts\v2\windows_dev.ps1 -Action start
```

설정이나 코드를 바꾼 뒤에는 위 순서로 재시작합니다. 웹 → API → 작업자 순서로 helper가 기록한 프로세스와 하위 프로세스를 종료한 뒤, helper가 시작한 DB에만 `pg_ctl -D var\pgdata -m fast -w stop`을 적용합니다. DB·문헌·대화 데이터 파일은 삭제하지 않습니다. API와 worker 종료는 강제 프로세스 종료이므로 진행 중 답변이나 색인·정리 작업이 끝나기 전에 끊길 수 있습니다. 웹에서 진행 중 요청을 취소하거나 완료를 확인하고, 처리 중 작업이 없는 때 종료하세요. 중단된 답변과 작업의 복구·재시도는 기존 서버 계약을 따릅니다.

DB를 별도 명령으로 이미 시작했다면 helper는 이를 재사용하고 `status`에 `외부 시작 DB 재사용, stop 대상 아님`으로 표시합니다. 이 경우 helper의 `stop` 후에도 DB가 유지됩니다. DB까지 helper로 관리하려면 먼저 해당 클러스터를 기존 방법으로 정상 종료하고 helper의 `start`를 실행하세요. 다른 PostgreSQL 서비스나 데이터 디렉터리에는 종료 명령을 사용하지 않습니다.

## RAG 실행 설정

API 코드만 갱신할 때는 답변 실행이 끝난 것을 확인하고 `pwsh -NoProfile -File scripts/v2/windows_dev.ps1 -Action restart-api`를 사용합니다. 기록된 API 프로세스 트리만 교체하므로 문헌 처리 작업자·DB·웹과 진행 중 그래프 구축은 유지합니다. 실행 중 답변은 API 재시작으로 중단될 수 있습니다.

작업자만 교체할 때는 `-Action restart-worker`, 인증 장애 등으로 반복 요청을 멈출 때는 `-Action stop-worker`를 사용합니다. 진행 중 작업은 중단될 수 있으므로 작업 ID·사용량을 먼저 보존하고, 복구 후 해당 실패만 기존 작업 재시도 기능으로 재개합니다. 두 동작 모두 API·DB·웹을 종료하지 않습니다.

로컬 `scripts/v2/dev.py serve|worker`는 비밀값 파일 `.env` 다음에 `.env.rag.local`의 문서 처리·검색 설정만 적용합니다. 이 파일에는 키·비밀번호를 넣지 않으며, 생성·인증·DB 설정은 덮어쓸 수 없습니다. 테스트와 일반 CLI는 이 파일을 자동 적용하지 않습니다. 실제 평가기는 명시적인 `--runtime-config .env.rag.local`로 같은 검색 설정을 사용합니다.

이번 로컬 설정은 Docling 2.143.0, BGE reranker v2 m3의 고정 판본(CUDA FP16, batch 2, 1,024 토큰, 후보 60개), Extended의 LightRAG를 사용합니다. 모델·런타임은 별도 `var/runtimes`, `var/models`에 두며 네트워크 없는 추론을 수행합니다. Docling PDF 변환은 최대 100쪽·300,000자·480초이며 공용 URL 다운로드의 5MB 한도는 유지합니다. 검증한 Cu 원문의 전체 페이지 OCR은 해당 로컬 반입 과정에서 명시적으로 적용했습니다. 향후 PDF의 OCR 기본값은 `OW_DOCLING_OCR`로 설정하고 추출 범위·수식·그림의 미확인 부분을 확인한 뒤 승인합니다.

원문 변환과 벡터 색인, 그래프 구축은 별도 과정입니다. 기존 임베딩은 입력 해시가 같으면 재사용하며 새 그래프는 승인된 판본과 메타데이터가 일치하고 전체 구축이 끝날 때 활성화합니다. 자료가 추가·정정되어 그래프 snapshot이 달라지면 관계 검색 불가를 명시하고 기존 벡터·문자 검색을 사용합니다. 자세한 보존·실패·재개 계약은 [Docling](DOCLING_INTEGRATION.md), [LightRAG](LIGHTRAG_INTEGRATION.md)를 따릅니다.

## 로그와 실패 확인

`var\windows-dev.json`은 helper가 소유한 PID와 생성시각 기록이며 `var\windows-dev.lock`은 동시에 helper를 실행하지 않게 하는 잠금 파일입니다. 실행 중에는 PID 기록을 삭제하거나 수정하지 마세요. 오래된 PID가 다른 프로세스로 재사용되었다면 생성시각·실행파일 검사가 일치하지 않아 종료하지 않습니다. 시작 중 일부 프로세스만 성공해도 실행 상태와 기록을 남기므로 원인을 수정하고 `start`를 다시 실행하거나 `stop`으로 정리할 수 있습니다.

API·worker·웹의 stdout/stderr는 각각 `var\api.stdout.log`, `var\api.stderr.log`, `var\worker.stdout.log`, `var\worker.stderr.log`, `var\web.stdout.log`, `var\web.stderr.log`에 기록됩니다. 각 프로세스를 새로 시작할 때 해당 로그가 덮어써집니다. DB 시작·종료 명령 로그는 `var\db-start.*.log`와 `var\db-stop.*.log`이며 DB 자체 로그는 `var\postgres.log`입니다. 필요한 오류 부분만 확인하고 비밀값을 포함한 로그 전체를 공유하지 마세요.

`start`는 최대 약 30초 동안 API health와 웹 HTTP 200을 확인합니다. 준비 확인에 실패하면 종료 코드 1을 반환하고 이미 시작한 프로세스는 유지합니다. `status`는 프로세스 소유 여부와 HTTP 정상 여부를 따로 보여줍니다. 포트 충돌 시 관련 프로세스의 명령과 소유자를 확인하여 기존 실행 방법으로 정리하고, PID만 보고 임의의 프로세스를 종료하지 마세요.

이 helper는 로컬 개발용이며 Windows 서비스 등록·자동 부팅·장애 자동 재시작을 제공하지 않습니다. 부모 프로세스가 비정상 종료되어 하위 프로세스만 남거나 PID 기록이 사라지면 helper가 그 프로세스의 소유권을 추측하지 않습니다. `status`, 포트와 실행 명령을 확인하여 원래 실행 방법으로 정리해야 합니다. 이번 Windows 환경의 설치·검증 기록은 [VERIFICATION.md](VERIFICATION.md)의 별도 기록과 함께 확인하세요.

## 준비된 자료와 첫 확인 순서

실행 모드는 `live`, 생성 모델은 `gpt-6-luna`, effort는 `medium`입니다. 서버 키는 사용자가 지정한 로컬 파일에서 `.env`로만 연결했습니다. 임베딩은 `text-embedding-3-large`의 직접 1536차원 `native` 프로필입니다. 평가 캐시는 제공되지 않아 예전 `3072 → prefix1536 + L2` 프로필을 사용하지 않았습니다.

제공된 129개 문헌 ZIP의 SHA-256은 기존 검증 기록의 `2b4c1e438414d10f997b7460112270329547d1c5fea97fd925453e4caac9117d`와 일치했습니다. 원본 ZIP과 기존 자료는 그대로 두고 미래인재 CLASS의 HBM·TSV, 하이피디아 TSV, 삼성 패키징 교육 문헌 3개만 정상 등록·개발용 승인·즉시 색인했습니다. 세 문헌은 `approved/ready`이고 11개 구간을 검색할 수 있습니다. 문헌별 자동 추출 3건과 대표 답변의 개인 위키 정리 1건도 성공했습니다. 이는 원문 진위나 의미 정확도의 전문가 인증이 아닙니다.

1. 로그인하고 `새 대화`를 눌러 위키·Extended OFF 기본값을 확인합니다.
2. 질문 초안을 입력하고 위키/분석·Extended를 바꾸며 초안과 선택 문헌이 유지되는지 확인합니다. 전환만으로 질문은 전송되지 않습니다.
3. `TSV가 HBM에서 어떤 역할을 하는지 보유 자료를 근거로 설명해 주세요. 확인할 수 없는 조건은 구분해 주세요.`를 보냅니다. 이미 같은 제목의 대표 대화와 실제 답변 1건을 저장해 두었습니다.
4. 답변의 관계 카드를 펼쳐 근거를 확인하고 출처 번호로 저장된 원문과 구간을 확인합니다.
5. 같은 대화에서 분석으로 바꿔 `TSV와 와이어 본딩의 차이를 연결 경로·전력·적용 한계별 표로 비교해 주세요.`를 이어갑니다. 브라우저의 기존 대표 대화에 이 초안을 준비했으며 아직 전송하지 않았습니다.
6. 필요할 때 Extended를 켜고 추가 내부 탐색과 부족한 근거 표시를 확인합니다. 원문의 구체 수치가 없으면 값이 없다는 답이 정상일 수 있습니다.
7. 외부 문헌 조사에서 문헌 하나의 확보 범위와 한계를 살펴보고 선택 자료를 원래 대화에 가져옵니다.
8. 개인 위키의 `HBM에서 TSV의 역할과 한계`를 열어 본문·연결 원문·원래 대화를 확인합니다.
9. 새로고침과 대화 이동 후 메시지·초안·선택 문헌·다음 요청 설정이 복원되는지 확인합니다.
10. 추가 질문을 실제로 보낸 경우에만 생성 중 취소와 명시적 재시도를 확인합니다. 취소·재시도도 공급자 사용량이 생길 수 있습니다.

이번 자동 확인은 대표 위키 질문 1회에 한정했습니다. 분석 표·Extended 실제 탐색·외부 조사 왕복·생성 중 취소/재시도의 새 실호출은 이어서 사용자가 확인할 범위로 남겼습니다. 과거 인계 검증과 현재 Windows에서 직접 본 범위를 구분합니다.
