# 문서 전처리 품질 개선 기록

후속 보완: [전처리 후속 기록](PREPROCESSING_FOLLOWUP_20261027.md)에서 XML 대표 근거 찾기, HBM2 표3~8의 해당 페이지 OCR·원문 대조 복원과 ALD 표1의 `aᵢ` 복원을 완료했다. 아래의 run-v4 보류 상태와 수치는 그 이전 판본의 기록으로 보존한다.

2026-10-27 한국 시간 기준. `fix/document-preprocessing-quality-20261027` 브랜치에서 오프라인 전처리만 수행했다. 서비스 등록·승인·활성화·색인과 외부 모델 호출은 수행하지 않았다. 기존 작업 폴더 `C:/Users/BISTelligence/ontology-wiki-conversation`의 미커밋 변경, 원본과 이전 처리 결과는 보존했다.

## 확인한 완료 지점과 구조

기준 커밋은 `5b5f6ed`다. 현재 작업 폴더의 `AGENTS.md`, README, ARCHITECTURE/API/DECISIONS, `CORPUS_QUALITY_REPORT_20261027.md`, `RAG_IMPLEMENTATION_CHECKPOINT_20261027.md`, Docling 안내와 최종 전처리 대장을 읽었다. 최신 미커밋 JATS 구현을 작업 브랜치에 복사하거나 다른 변경과 함께 커밋하지 않았다.

기존 검토·정정 결과는 `var/corpus-quality/20261026T073106Z/review/reconciliation-20261027/final-service-ledger.json`, 기존 PDF/XML 추출·좁은 독립 검수는 `var/verification/docling-20261027/`와 `batch/`에서 원본 해시를 대조해 재사용했다. 과거 승인·색인 상태는 이번 처리본의 승인으로 승계하지 않는다.

`knowledge.documents.preprocessing`은 문단·표 보존, 제한된 추출 정정, XML 원문 위치와 참조 연결을 담당한다. `scripts/v2/preprocess_documents.py`는 해시가 고정된 입력을 읽어 새 폴더에 원본·입력·처리본·구간·수정 기록을 쓴다. 기존 `prepared_passages()`의 위치 검증을 재사용한다. API, Repository, DB, 검색·리랭커·답변·LightRAG와 연결하지 않았다. 새 의존성은 추가하지 않았다.

## 발견한 문제와 수정

| 문제 | 수정과 적용 범위 |
| --- | --- |
| Markdown의 글자수 overlap이 문장·표를 중간에서 자를 수 있음 | 기존 1,400자 설정을 목표로 절·문단·표·코드 블록 단위로 구간화. 긴 구조는 임의 절단하지 않고 이웃 구간 ID를 제공. 기존 편집본 121개에 적용 |
| `원문·편집 계보` 부록이 기술 검색 구간에 섞임 | 명시적인 편집 부록만 별도 보존. 374개 블록을 `editorial-notes.md`와 위치 기록으로 분리. 필자·회사 면책·별표 용어 주석·기술 조건은 본문에 유지 |
| HBM2 논문의 표 열이 1~2열로 평탄화되고 다음 구간에 캡션·조건 누락 | 원문 p5 표1/2, p23 표9/10의 모든 복원 행을 native PDF 텍스트와 대조하고 해당 페이지를 시각 확인. 열 제목·단위·캡션을 유지하고 이어지는 표 구간에도 캡션 반복 |
| TSV/TGV JATS 그림7/12 캡션의 삽입손실 기호 누락 | 원본 MathML의 `msub(S,21)`에 근거해 `insertion losses ()`를 `insertion losses (S₂₁)`로 복원. XML ID·XPath와 수정 전후를 기록 |
| JATS 위치가 공통 절 제목과 Docling 내부 참조에 머무름 | 고유하게 대응하는 캡션과 완전한 문단에 원본 XML ID·XPath를 추가. 본문 xref와 표·그림 구간을 양방향으로 연결. 부호·소수점을 유지하는 대응 비교를 사용 |
| Windows 파일 저장 시 LF/CRLF 변환으로 해시·위치 불일치 | 원문 Markdown의 CRLF를 읽을 때 보존하고 산출물을 UTF-8 바이트로 저장. 실제 저장 파일의 해시와 모든 구간 slice를 다시 검사 |

원문 내용 정정은 새로 하지 않았다. 기존에 검토한 편집본과 정정 기록을 재사용했다. ALD 원문의 §3/표4 `10/20 sccm`와 §4.4 `10→50 sccm` 상충은 추출 오류와 구분해 그대로 남겼다. 복잡한 MathML·표 구조를 추측해서 복원하지 않았다.

## 대표 문서 전후 비교와 검수

다음 판정은 적어 둔 부분에만 적용한다. ‘통과’는 전체 논문 내용·과학적 정확성·이용 권한·실제 검색 성공의 인증이 아니다. 정량 실험이나 표가 없는 문서의 해당 항목은 ‘확인 불가’로 기록했다.

| 대표 문서 | 전후 비교 | 핵심 본문 | 수치·단위 | 표 행·열 | 조건·결과 | 출처·위치 |
| --- | --- | --- | --- | --- | --- | --- |
| e096 삼성 포토공정 | 편집 부록이 섞인 8구간 → 기술 구간 7개와 별도 편집 부록. PR 양성/음성·다음 식각 연결 보존 | 통과 | 확인 불가 | 확인 불가 | 확인 불가 | 통과 |
| e128 하이브리드 본딩 편집본 | `정 여유가 줄어든다…`라는 문장 중간 시작 → 문단 전체와 이웃 연결. 필자·별표 주석·면책 유지 | 통과 | 통과 | 확인 불가 | 확인 불가 | 통과 |
| d001 ALD JATS | 별도 배치 표의 공통 위치 → 표4 XML ID·XPath와 본문 참조. 원본 표4 5행×4열 20셀 일치 | 확인 불가 | 통과 | 통과 | 통과 | 통과 |
| m001 HBM2 PDF | 표10 1열 → Chip / IDD4R(mA) / Our pattern(mA) / Increase(%) 4열. 후속 구간에도 35 chips·평균±표준편차 유지 | 확인 불가 | 통과 | 수정 필요 | 통과 | 통과 |
| p003 TSV 검출기 PDF | 기존 선택적 OCR 재사용. pp4~5의 5.4%/3%, 2.6%/3.1% FWHM·외부 펄서·약1 mm 조건과 페이지 대조 | 확인 불가 | 통과 | 확인 불가 | 통과 | 통과 |
| t001 TSV/TGV JATS 추가 대조 | 그림7/12의 빈 괄호 → 원문 기호 S₂₁. 시뮬레이션과 측정 캡션을 각각 보존 | 확인 불가 | 통과 | 확인 불가 | 통과 | 통과 |

e096/e128은 기존 편집본의 문자 보존과 지정 구절을 대조했다. d001은 기존 독립 검수의 §3·표4·§4.4를 재사용하고 표4 원본 셀을 직접 대조했다. m001은 p5/p23, p003은 pp4~5를 시각 대조했다. t001은 원본 XML의 지정 캡션과 MathML을 대조했다. 그 밖의 쪽·모든 수식·그림 픽셀을 새로 전수 검증하지 않았다.

## 전체 적용 범위와 미확인 부분

- 기존 정정편집본 121개와 Docling 추출본 13개, 합계 134개 처리본에서 998구간을 보존했다. 기존 출처 결함 8문헌과 연구 자료의 대체 표현·메타데이터·보류 자료 19개를 합친 27개 제외 항목도 해시·사유와 함께 대장에 유지했다. 중복 표현을 독립 문헌으로 세지 않았다.
- 색인 검토 후보는 977구간이다. m001 표3~8은 행·열 병합을 안전하게 복원하지 못했으므로 21구간에 보류 사유를 기록하고 후보 파일에서 제외했다. 원문과 전체 처리본에서는 삭제하지 않았다.
- XML 원문 위치가 직접 연결된 구간은 140개다. XML 문단 94개는 수식 표현 차이·구간 경계·중복 등으로 완전하고 고유한 문자열 대응을 확정하지 못했다. 이는 누락 94건이라는 뜻이 아니며 해당 XPath를 검토 목록에 남겼다. 복잡한 캡션 수식 1개도 원본을 보존하고 확인 대상으로 남겼다. 모든 구간의 추출본 위치와 Docling 참조는 따로 유지한다.
- Markdown의 1,400자는 구조를 훼손하지 않는 목표 크기다. 기존 Docling의 768토큰 구간은 재사용했다. 표·긴 문단 때문에 큰 구간이 남아 있으며 최적 크기를 찾는 실험은 하지 않았다.
- 같은 원자료의 XML을 사용할 수 있는 경우 기존 JATS 결과를 사용했다. OCR은 기존 Cu 및 p003 결과만 재사용했고 추가 일괄 OCR·다운로드·모델 설치는 하지 않았다. 스캔·그림 내부 숫자의 전수 판독은 미완료다.
- 새 처리본은 모두 `offline_review_candidate`이며 기존 승인 상태를 승계하지 않는다. 후보 파일은 다음 색인 검토의 입력이고 서비스 승인·등록·색인·활성화를 실행하는 명령이 아니다. 이 대장 밖의 신규 수집 자료를 전수 처리했다고 주장하지 않는다.

## 산출물

최종 실행 폴더는 `C:/Users/BISTelligence/ontology-wiki-preprocessing/var/preprocessing-quality-20261027/run-v4`다. 원문·외부 자료 본문은 Git 제외 폴더에 보관했다.

| 파일 | 용도 |
| --- | --- |
| `input-manifest.json`, `run-ledger.json`, `artifact-hashes.json` | 원본/입력 SHA-256, 판본·계보·출처·처리 및 제외 범위, 산출물 해시 |
| 문헌별 `original.*`, `input.*`, `extracted.md` | 원본 바이트, 사용한 기존 편집본/Docling JSON, 정정 전 추출문 구분 |
| 문헌별 `clean.md`, `passages.json`, `source-map.json` | 정리 본문·검색 구간·Unicode 문자 위치·원문 페이지/좌표/Docling 참조/XML 위치·이웃 및 참조 구간 |
| 문헌별 `editorial-notes.md`, `editorial-map.json`, `corrections.json` | 검토 부록·위치와 추출 정정 전후/근거. 원본의 내용 오류와 구분 |
| 문헌별 `provenance.json`, `xml-mapping-review.json` | 처리 판본·이전 서비스 판본·확인 범위·미대응 XML 위치 |
| `prepared-passages.jsonl` | 보류 구간까지 포함한 전체 998구간 보존본 |
| `index-candidates.jsonl` | 알려진 손상 표 21구간을 제외한 977개 색인 검토 후보 |

같은 상위 폴더의 `review-v4/QA.md`, `representative-qa.json`, `before-after.md`, `mechanical-validation.json`, `independent-review.json`과 원문 렌더가 검수 기록이다. `run-status.json`이 최신 실행을 가리킨다. 이전 run-v1~3은 수정하거나 삭제하지 않았다. 특히 run-v1은 줄바꿈 오류로 기각한 과거 실행이므로 사용하지 않는다.

재현은 기존 API 가상환경의 Python으로 아래 CLI를 실행하되 기존 출력 폴더와 다른 새 경로를 지정한다. 입력 해시가 바뀌거나 출력 폴더가 이미 있으면 거부한다. Docling 모델·생성·임베딩은 실행하지 않는다.

```powershell
Set-Location -LiteralPath 'C:\Users\BISTelligence\ontology-wiki-preprocessing'
& 'C:\Users\BISTelligence\ontology-wiki-conversation\.venv\Scripts\python.exe' -B -X utf8 scripts/v2/preprocess_documents.py --manifest var/preprocessing-quality-20261027/input-manifest-v3.json --output var/preprocessing-quality-20261027/new-review-run
```

## 코드·산출물 검증

`python -B -X utf8 -m pytest backend/tests/test_offline_preprocessing.py backend/tests/test_document_parsers.py -q`가 14개 통과했다. 문단·표·코드·의미 있는 주석 보존, CRLF 원문 위치·실제 저장 파일 해시, XML 외부 엔터티 거부, 기호 복원과 참조, 표 미검토 행·부호 변경·누락 거부, 해시 불일치·기존 출력 덮어쓰기 거부를 검사한다. DB·실제 공급자 호출은 없다.

최종 실행은 입력·원본 사본·처리본 해시, 저장 파일의 998구간 위치, Markdown 121개 전체 비공백 문자 커버리지, ALD 표4 20셀과 산출물 1,478개 해시를 확인했다. 별도 읽기 전용 검토도 같은 해시·위치·977후보/21보류 분리와 원본 XML 대응 캡션 113개의 숫자를 확인했고, 발견한 줄바꿈·표 행 삭제/부호·코드 블록 오인 문제를 수정한 뒤 추가 지적이 없었다.

서비스 API·DB·검색·답변·성능은 이번 변경으로 검증하지 않았다. 신규 임베딩·답변 생성·대규모 AI 평가·그래프 구축·서버 재시작·배포·원격 push는 수행하지 않았다.
