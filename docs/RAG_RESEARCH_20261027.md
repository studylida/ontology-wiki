# 검색·출처·문헌 처리 선행 자료 조사

후속 결정: 이 문서는 선행 조사 기록이다. LightRAG는 동일 자료 소규모 비교 이후 사용자 지시로 제거됐으며 현재 도입 후보나 실행 환경이 아니다. [비교 결과](RAG_LIGHTRAG_SUBSET_COMPARISON_20261027.md)를 참고한다.

2026-10-27 사용자의 요청에 따라 Agent Reach의 GitHub 채널과 공개 원문을 확인했다. 아래는 도입 후보 및 조사 결과이며, 이 프로젝트에서 각 도구의 성능을 입증했다는 뜻은 아니다.

## 현재 서비스와 LightRAG

현재 서비스는 PostgreSQL 벡터·문자 검색과 승인된 문헌 판본, 근거 구간, 자동 추출된 개념·관계를 결합한다. [LightRAG](https://github.com/HKUDS/LightRAG)는 엔터티·관계 그래프와 세부·전역 검색을 제공하며 [논문](https://aclanthology.org/2025.findings-emnlp.568/)에서 해당 방법을 설명한다. 관계 질의의 후보이지만, 자료별 승인·철회·접근권한과 판본별 구간 출처가 현재 서비스와 동일하게 보존된다고 가정할 수 없다.

공식 PyPI의 `lightrag-hku==1.5.7`을 별도 Python 3.12 가상환경과 저장 공간에 설치해 공개 논문 기반 편집 요약 세 건을 시험했다. 두 번째 시도에서는 임베딩 입력 100개라는 시험 상한 때문에 한 건만 색인됐고, 질문과 품질 비교는 실행하지 못했다. 1차 실패의 정확한 이유와 사용량은 확인하지 못했다. 성공적인 채택 근거가 아니며 기존 색인을 교체하지 않았다. 상세 결과는 로컬 `var/corpus-quality/20261026T073106Z/review/lanes/lightrag-poc/result.md`에 있다.

동일한 승인 문헌과 질문을 쓰는 후속 비교에서는 실험 결과·조건 동시 회수, 구간별 인용 정확성, 무관 문맥, 사용자·판본 권한, 철회 이후 잔존 여부, 시간과 모델 사용량을 함께 검토해야 한다. 소규모 재현으로 이러한 계약을 확인하기 전에는 제품에 연결하지 않는다.

## 전처리와 평가 후보

- [Docling](https://github.com/docling-project/docling): PDF의 문서 구조·표 추출을 검토할 후보다. 현재 PDF에서 표와 도표의 수치·단위·캡션이 함께 보존되는지 비교 실험이 필요하다. 공개 저장소의 라이선스는 MIT다.
- [RAGChecker](https://github.com/amazon-science/RAGChecker): [논문](https://arxiv.org/abs/2408.08067)은 검색에서 필요한 주장 회수와 답변의 근거 충실성·잡음 민감도를 구분한다. 한국어 반도체 기준 답안과 평가 모델의 검증 및 비용 확인이 필요하다. Apache-2.0이다.
- [ALCE](https://github.com/princeton-nlp/ALCE): [논문](https://arxiv.org/abs/2305.14627)은 답변 정확도와 인용의 정확성·완전성을 구분한다. 구형 의존성과 영어 중심 평가가 현재 환경과 한국어 질문에 적합한지는 미검증이다. MIT다.
- [Microsoft Azure RAG 샘플](https://github.com/Azure-Samples/azure-search-openai-demo): [평가 코드](https://github.com/Azure-Samples/azure-search-openai-demo/blob/main/evals/evaltools/eval/evaluate_metrics/code_metrics.py)는 답변 길이, 인용 존재, 예상 출처 일치를 나누어 평가한다. 인용 존재만으로 해당 주장의 근거가 올바르다는 뜻은 아니다. MIT다.

공개 저장소는 읽고 비교했으며 Docling·RAGChecker·ALCE는 이 서비스에 설치하거나 통합하지 않았다. 사용자 문헌에 대한 처리 권한과 모델 전송 범위는 자료별로 확인해야 한다.

## TSV와 와이어 본딩 관련 추가 근거

[ThruChip 2014 발표](https://web.stanford.edu/class/ee380/Abstracts/141022-slides.pdf)의 21쪽은 핀 간 전송과 8개 메모리 칩·1개 SoC의 버스 전송을 구분해 TSV와 와이어 본딩의 pJ/bit 수치를 제시한다. 예를 들어 32nm 핀 간 행에는 각각 0.35와 3.45 pJ/bit가 있다. 해당 표만으로 두 방식이 동일 전압·속도·부하에서 실측됐는지 또는 어떤 모델을 사용했는지는 확인되지 않는다. 다른 발표판을 독립 연구로 중복 집계하지 않는다.

[Nagarajan 등의 광 트랜시버 논문](https://doi.org/10.1109/JSTQE.2022.3214418)은 세 패키지 경로의 삽입 손실을 HFSS로 시뮬레이션한다. 이 비교는 전력 실측이 아니며, 논문의 시스템 집적 전망치를 TSV와 와이어 본딩의 동일 조건 전력 차이로 바꿔 쓰지 않는다. 원문의 그림 수치와 사용 조건은 별도로 확인한다.
