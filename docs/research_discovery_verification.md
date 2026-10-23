# 탭4 구현 검증 결과

검증일: 2026-10-23 (Asia/Seoul). 운영 DB·원문·인증 파일을 복사하거나 수정하지 않았다. 원본 저장소의 기존 미커밋 소스를 읽기 전용 기준으로 복사하고, 별도 소스 작업 폴더와 메모리 DB에서 검증했다.

## 변경

기존 계층 안에서 질문 해석과 필요한 확인, 다중 검색어 검색·보완 검색, 확보 구간 기반 문헌 평가와 문헌별 설명을 연결했다. 문헌 소개·포함 이유·활용점·한계와 원문 구간을 구분한다. 보류·제외·서지정보 전용 자료는 새 조사의 후속 근거에서 차단한다. 과거 세션과 기존 발췌는 보존하고 종합 분석 후에도 조사·비교 맥락을 유지한다. 관련성 백분율과 미사용 고정 조사 Clarifier를 정리했다.

## 통과한 검사

- `python scripts/verify_research_discovery.py`: HBM 질문 해석, 포함·보류·제외, 문헌별 설명, 구간 ID 검증, 보완 검색과 중복 검색 종료, 과거 세션 조회·분석, 비교 맥락 복원, 실패·부분 결과 처리. 모델·Crossref 응답은 모의이며 DB는 메모리다.
- `python scripts/verify_research_discovery.py --regression`: 기존 `verify_research_flow.py`를 수정하지 않고 검색 계획·평가만 모의하여 종합 분석→티켓→검토·승인과 비교 왕복을 검증했다. 검토·승인은 격리 메모리 DB에서만 수행했다.
- 독립 리뷰 후 회귀: 6000자 초과 등록 발췌의 원형 보존과 티켓 성공, DOI URL 통합과 등록 ID 우선, 후속 검색의 새 문단 재평가, 일반 URL의 문헌 식별 쿼리 구분, 같은 DOI의 여러 Markdown을 한 카드로 통합.
- Vite production build 통과. 기존 번들 크기 경고는 남아 있다.
- 전용 루프백 프론트 13004 / 백엔드 18004에서 실제 브라우저 조작: HBM 질문 입력→질문 해석→설명 카드→근거 펼치기→보류·제외 선택 불가→선택 문헌 종합 분석→탭 왕복 후 상태 유지. 고정 fixture 외부 응답으로 검증했다.

## 실제 외부 접속과 미확인 범위

실제 Crossref에 `HBM hybrid bonding yield defects`를 요청해 8건, 초록 2건을 확인했다. 예시 제목은 `Deep Convolution Neural Networks for Automatic Detection of Defects which Impact Hybrid Bonding Yield`, `D2W Hybrid Bonding Challenges for HBM`, `YAP+: Pad-Layout-Aware Yield Modeling and Simulation for Hybrid Bonding`이다.

격리 환경의 실제 Gateway 질문 해석 요청은 결과를 생성하지 못했다. 키 값이나 인증 파일은 검사하지 않았다. 실제 모델과 실검색을 결합한 설명 정확도·소요 시간은 미확인이다. 모의 API의 OpenAI 경로 로그는 실제 유료 모델 호출 증거가 아니다. 외부 출판사 전문 자동 확보와 HBM 양산 적용성은 검증하지 않았다.

## 기존 변경과 커밋 범위

원본 `fix/wiki-knowledge-flow` 작업 폴더에는 관련 파일을 포함해 여러 미커밋 변경과 미추적 파일이 존재한다. 원본의 파일·인덱스·브랜치는 그대로 보존한다. 새 로컬 작업 브랜치의 커밋은 변경 전 소스 대비 이번 작업의 차이만 선별하며 다른 작업을 함께 커밋하지 않는다. 따라서 커밋 SHA만 단독으로 깨끗한 checkout에 적용한 상태는 이번 검증 상태가 아니다. 검증된 전체 소스는 분리 작업트리에 있고, 그 안에도 기존 선행 미커밋 변경이 남는다. 새 DB 마이그레이션·원격 push·배포·운영 위키 적용은 수행하지 않는다.

작업 중 별도 세션의 검토 센터 코드·지침 갱신이 관찰되었다. 원본에는 쓰지 않고 갱신된 소스를 격리 환경에 반영한 뒤 관련 검사를 다시 수행했다.
