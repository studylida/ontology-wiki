# 공개 문헌 확보와 검증 환경

## 기본 경로와 명시적 egress 선택

공개 문헌 본문 확보의 기본 설정은 `OW_RESEARCH_NETWORK_MODE=system`입니다. 시스템 DNS로 공개 주소를 확인하고, 반환된 모든 IP를 검사한 뒤 선택한 IP에 HTTPS로 연결합니다. 원래 호스트의 `Host`·TLS SNI·인증서 검증을 유지하고, 이동한 URL도 다시 검사합니다.

현재 실행 환경은 일반 공개 호스트의 시스템 DNS가 `gaierror(-3)`로 실패하고 지원 egress 프록시를 통해 외부 HTTPS에 접근하는 구조입니다. 이 조건에서 사용할 수 있도록 다음 **명시적인 선택 경로**를 추가했습니다.

```dotenv
OW_RESEARCH_NETWORK_MODE=google_doh_egress
```

이 설정은 `ResearchService.fetch()`가 `integrations/public_egress.py`의 resolver·transport를 선택하도록 합니다. 기본값을 바꾸거나 DNS 실패 시 자동으로 이 경로로 전환하지 않습니다. 모델·effort·문헌 범위·권한에는 영향을 주지 않습니다.

실행 환경에는 승인된 `HTTPS_PROXY` 또는 `https_proxy`가 있어야 합니다. 현재 어댑터가 지원하는 것은 사용자명·비밀번호가 URL에 포함되지 않은 HTTP egress 프록시입니다. 프록시 주소나 자격증명을 HTTP 요청 DTO에서 받지 않으며 로그·응답·검증 보고에도 넣지 않습니다. 지원하지 않는 설정은 `research_network_configuration`으로 중단합니다.

선택 경로의 처리 순서는 다음과 같습니다.

1. 원래 URL이 사용자명·비밀번호 없는 공개 HTTPS 주소이며 포트가 443인지 확인합니다. 비공개 IP 리터럴은 네트워크 요청 전에 거절합니다.
2. [Google Public DNS의 공식 DoH JSON API](https://developers.google.com/speed/public-dns/docs/doh/json)에 해당 호스트의 **A와 AAAA를 각각** 조회합니다. 질문·응답 상태·잘림 여부를 검사하고 모든 IP가 `is_global`인지 확인합니다. 비공개 주소가 하나라도 섞이면 전체 요청을 거절합니다.
3. 이 DNS 응답에서 얻은 IP를 egress 프록시의 `CONNECT IP:443` 대상으로 사용합니다. 프록시에 원래 호스트의 DNS 해석을 다시 맡기지 않습니다. 코드나 설정에 문헌 서버 IP를 하드코딩하지 않습니다.
4. 터널 위의 HTTPS는 원래 호스트 이름으로 SNI와 인증서 호스트 검증을 수행하고 같은 `Host` 헤더를 보냅니다. HTTPX의 공개 SSL context API로 실행 환경의 신뢰 CA를 반영하며 인증서 검증을 끄지 않습니다.
5. 기존 `fetch_public()`이 이동 대상 재검사, 최대 이동 횟수, 형식·5MB 제한을 적용합니다. 기존 파서가 본문 확보 범위를 판정합니다.

공식 DoH·egress·TLS·원문 서버 중 어느 단계에서 실패하더라도 공개 IP 검사를 생략하거나 다른 프록시·IP·호스트로 재시도하지 않습니다. 사용자에게 명시적인 오류를 반환합니다. DNSSEC의 `AD=false`는 실제 기록 그대로 남기며, 서명되지 않은 DNS 응답을 DNSSEC 인증 완료로 표시하지 않습니다.

### 프록시와 TLS 구현 이유

현재 고정한 httpcore 1.0.9의 일반 HTTP proxy 경로는 TLS 서버 이름으로 URL의 host를 사용합니다. 공개 IP로 고정한 URL을 그 경로에 바로 넣으면 원래 도메인의 SNI·인증서 검사와 맞지 않습니다. 이 구현은 공개 `AsyncNetworkBackend`와 `AsyncConnectionPool` 인터페이스를 사용하여 IP CONNECT 터널을 제공하고, 일반 TLS 연결이 `sni_hostname`을 존중하도록 합니다. 인증서 검증을 끄는 해결법은 사용하지 않습니다.

DoH 요청의 프록시는 명시적으로 고정합니다. 그와 별도로 `httpx.create_ssl_context(verify=True, trust_env=True)`로 신뢰 CA 설정만 반영합니다. `SSL_CERT_FILE` 또는 `SSL_CERT_DIR`을 제공하는 환경에서는 해당 CA 구성을 사용하며, 이 동작은 [HTTPX 환경변수 문서](https://www.python-httpx.org/environment_variables/)의 의미를 따릅니다. `trust_env=False`만 적용하여 환경 CA까지 빠뜨렸던 검증 실패 기록은 `verification/research-fetch-egress-tls-config-attempt.json`에 남겼습니다.

컨테이너에서도 이 선택 경로를 사용하려면 허용된 egress 설정과 신뢰 CA를 컨테이너에 명시적으로 전달해야 합니다. 호스트의 프록시 주소나 CA 경로가 컨테이너에서도 그대로 유효하다고 가정하지 않습니다. 기본 Compose 실행에 이 환경 전용 주소를 넣지 않습니다.

## 실제 확보·파싱 재현

아래 스크립트는 제품의 실제 fetch·파서를 사용하지만 DB 저장이나 모델 호출을 하지 않습니다. API 로그인·관련성 생성·문헌 첨부까지의 성공과는 별도 검증입니다.

```bash
.venv/bin/python scripts/v2/verify_external_fetch.py \
  --url https://www.lamresearch.com/technical-glossary/ \
  --network google-doh-egress \
  --output /path/to/fetch-result.json
```

기본 시스템 DNS 경로를 재현하려면 `--network system`을 사용합니다. CLI 옵션은 검증 실행에만 적용되며 서버 설정을 쓰거나 변경하지 않습니다. 성공은 종료 코드 0, 차단·실패는 종료 코드 1입니다.

`verification/research-fetch-egress.json`에 기록한 실제 결과는 다음과 같습니다.

| 항목 | 결과 |
| --- | --- |
| 대상 | Lam Research Technical Glossary |
| 처리 경로 | 공식 Google DoH → 공개 IP CONNECT → 원래 Host/SNI의 HTTPS → 기존 파서 |
| 원문 HTTP 응답 | 200 |
| 원문 크기 | 664,804 bytes |
| 원문 SHA-256 | `f0fe64e2e83740f0b467889b3f531e3f2ddae8e897982a8243a7c7f13083adc8` |
| 추출한 본문 | 30,371자 |
| 확보 범위 | `partial`: 동적 내용·이미지·표의 완전성 미확인 |
| 모델·DB | 모델 호출 0회, DB 쓰기 없음 |

사이트 내용과 DNS 응답은 바뀔 수 있습니다. 위 숫자는 해당 검증 시점의 결과이며 후속 실행에서 동일한 바이트를 강제하지 않습니다. 이 결과로 문헌의 모든 내용이나 생성 답변의 의미 정확성을 인증하지 않습니다.

회귀 테스트는 다음 명령으로 실행합니다.

```bash
PYTHONPATH=backend .venv/bin/python -m pytest \
  backend/tests/test_public_fetch.py backend/tests/test_public_egress.py \
  -q --tb=short
```

27개 테스트가 통과했습니다. 공개/비공개 A·AAAA 혼합, 잘못된 DoH 질문·상태, DoH 거절, 사설 주소로의 이동, IP CONNECT, 원래 Host/SNI, 인증서 검증 유지, CONNECT·TLS 실패 시 무재시도, 서비스의 명시적 설정 선택을 검사합니다. 이 테스트들은 네트워크 fake를 사용하며 실제 네트워크 호출 결과와 구분합니다.

## Docker 실행 환경의 현재 상태

`scripts/v2/check_runtime_prerequisites.py`는 설치·시작·DB 접속 없이 도구·소켓·권한·rootless namespace를 확인합니다. 앱의 `.env`나 공급자 키를 읽지 않습니다.

```bash
.venv/bin/python scripts/v2/check_runtime_prerequisites.py \
  --output /path/to/container-runtime-prerequisites.json
```

현재 환경에서 얻은 결과는 `verification/container-runtime-prerequisites.json`에 있습니다.

- Docker·dockerd·Podman·containerd·runc 및 관련 daemon socket이 없습니다.
- user/mount/network/pid namespace의 생성 가능 여부는 확인했지만, rootlesskit·newuidmap·newgidmap·slirp4netns가 설치되지 않았습니다.
- 현재 실행 컨텍스트에는 `CAP_SYS_ADMIN`·`CAP_NET_ADMIN`이 없습니다. rootless namespace 지원만으로 일반 Docker daemon을 실행할 수 있다고 판단하지 않습니다.
- `compose.dev.yml`의 YAML과 참조 Dockerfile 존재는 확인했습니다. Docker Compose 자체의 config 검증, 이미지 build, 컨테이너 startup은 이 진단 결과에 포함되지 않습니다.

[Docker의 공식 rootless 설치 조건](https://docs.docker.com/engine/security/rootless/)에는 UID/GID 매핑 도구와 subordinate UID/GID 구성이 포함됩니다. 현재 도구를 설치하거나 시스템 설정을 바꾸는 작업은 수행하지 않았습니다. 승인된 Docker 실행 환경에서 README의 개발용 절차로 build·기동·마이그레이션·대표 API 흐름을 실제 실행한 결과가 있어야 Docker 검증 완료로 표시할 수 있습니다. 시스템 도구 부재와 앱의 컨테이너 실행 결함을 같은 원인으로 단정하지 않습니다.

같은 검증을 표준 GitHub Actions 러너에서 수행하는 개발용 workflow와 재현 스크립트도 추가했습니다. 실행 범위·정리·fixture 실패의 취급은 [COMPOSE_SMOKE.md](COMPOSE_SMOKE.md)를 따릅니다. 실제 Actions 결과는 로컬의 환경 진단과 별도로 확인합니다.
