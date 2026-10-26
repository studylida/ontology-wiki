# 이후 개발자를 위한 변경 지점

## 생성 모델 또는 공급자 변경

1. 확인된 API 모델 ID·계정 가용성·요금/조건을 검증합니다. 현재 모델을 사용할 수 없다는 이유만으로 다른 모델에 묵시적으로 fallback하지 않습니다.
2. 같은 OpenAI Responses 모델이면 `OW_GENERATION_MODEL`, 필요시 `OW_GENERATION_EFFORT`를 변경합니다. 모델이 지원하지 않는 effort를 임의로 보정하지 않습니다.
3. 공급자 프로토콜이 다르면 `integrations/providers.py`의 GenerationClient Protocol에 맞는 어댑터를 추가하고 startup factory에서 선택합니다. feature Service/Controller에 공급자 SDK를 퍼뜨리지 않습니다.
4. 실제 delta·완료·실패·취소·usage를 매핑하는 계약 테스트를 만듭니다. 본문 없는 상류 이벤트와 첫 실제 본문을 구분합니다.
5. 고정 질문/근거로 의미 품질을 비교합니다. fixture 성공이나 모델의 self-confidence를 품질 검증으로 사용하지 않습니다.

## 임베딩 변경

모델·API 차원·저장 차원·변환·버전이 하나의 프로필입니다. 현재 vector 컬럼은1536차원입니다. 차원을 바꾸려면 별도 migration과 새 프로필 저장 공간이 필요합니다. input_hash는 실제 embedding_text에 대해 계산합니다. 같은 text/profile/scope만 캐시 재사용이 가능합니다.

공용 문헌 프로필 변경은 별도 색인/검증 후 활성 운영 설정을 전환합니다. 캐시 반입 명령은 해당 모델의 고정 입력/ID/차원을 검사합니다. 기존 source body나 원문 판본은 변경하지 않습니다.

## 답변 형식 추가/수정

`rag/dto.py`의 responseMode, `answers/prompt.py`, FE `types/contracts.ts`, `services/conversationService.ts`, `views/components/MessageCard.tsx`가 주요 변경 지점입니다. 검색 Service·권한·모델 설정을 응답 형식에 결합하지 않습니다. 기존 답변의 제출 모드와 본문은 보존합니다.

위키는 핵심 설명 → 목적·원리 → 사례·조건 → 관계 → 출처·부족한 부분입니다. 관점 카드는 사례·조건에 들어갑니다. 표와 본문은 안전한 Markdown으로 렌더하고 source 링크는 허용된 실제 citation ID만 사용합니다.

## 출처 유형/관점 추가

문헌 metadata의 publisher/author/attributedTo/attributionBasis/sourceType을 먼저 정의합니다. 기관 도메인만으로 귀속을 확정하지 않습니다. `documents`의 접근/수정, `ontology/extraction.py`의 입력/결과 DTO, `ontology/repository.py`의 현재 버전 검사, FE Evidence 카드의 표시를 함께 확인합니다.

새 source view는 approved public source만 받아야 합니다. 개인 질문·조건은 canonical concept/aspect 선택을 돕는 데만 사용하고 공용 설명 생성 입력에는 포함하지 않습니다. 귀속 변경은 기존 요약 무효화와 재추출을 필요로 합니다.

## 관계 타입 추가

방향, 성립 조건, 역방향 해석, 여러 근거의 의미를 먼저 정의합니다. `is_a`와 `part_of`를 같은 상하위로 합치거나 유사도로 `alternative_to`를 만들지 않습니다. 추출 DTO와 prompt, Repository의 가시성, UI 라벨, 외부 API 계약을 같은 변경에서 갱신합니다. 모든 문헌의 완전한 그래프화를 기본 검색 조건으로 만들지 않습니다.

## 저장 모델 변경

적용된 SQL migration은 수정하지 않습니다. `backend/migrations/v2/`에 새 파일을 추가하고, Entity와 실제 migration 양쪽을 검증합니다. 테스트의 metadata.create_all만 통과하고 migration은 실행하지 않은 상태를 완료로 보고하지 않습니다. 운영 이전은 이 구현의 승인 범위 밖입니다.

## 애니메이션 변경

https://transitions.dev/의 실제 패턴을 확인하고 참고한 URL을 문서에 남깁니다. 작은 CSS 전환으로 충분하면 새 런타임을 추가하지 않습니다. reduced-motion, 키보드 포커스, 화면 폭 변경을 확인하며 가짜 진행률·가짜 타이핑을 만들지 않습니다.
