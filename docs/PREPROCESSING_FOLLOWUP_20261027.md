# 전처리 후속 보완

2026-10-27 한국 시간. 기존 `run-v4`와 원본을 보존하면서 요청한 세 항목만 처리했다. 현재 산출물은 `C:/Users/BISTelligence/ontology-wiki-preprocessing/var/preprocessing-quality-20261027/followup-v1/`의 `m001-v2/`, `d001-v2/`다. 전체 코퍼스를 다시 처리하거나 새 임베딩·답변 생성·그래프 구축·서비스 자료 교체·승인을 실행하지 않았다.

## XML 연결이 없는 구간의 근거 찾기

자동 XML 문단 연결이 없는 네 구간에서 기존 절 이름과 발췌문으로 보존 원본의 유일한 문단을 실제 찾았다. 저장된 DOI와 원본 XML의 DOI도 일치했다. 확인한 절 ID는 검수 증거로만 기록했고 해당 구간의 XML 위치를 추정하거나 새로 붙이지 않았다.

| 문헌·기존 구간 | 기존 절 이름과 검색 발췌문 | 원본에서 확인한 내용 |
| --- | --- | --- |
| d001 ordinal 8 | §2.2 Analysis of Variance (ANOVA), `To test the above hypotheses` | 해당 ANOVA 문단과 식(7) MathML |
| d001 ordinal 13 | §2.3 Full Factorial Design of Experiments, `The four factors are deposition temperature` | 네 요인·각 2수준·2반복·16실행·Table 2 참조 |
| b004 ordinal 7 | §3.1.1 Electrical Resistance Measurement, `With the same bonding temperature` | 300°C/90 MPa에서 60→5 s, 300°C/10 s에서 90→15 MPa 및 약4.5 mΩ |
| tc001 ordinal 4 | §2.3 Bonding Process, `The bonding process was conducted` | 300°C·1/2 h·1.33×10⁻¹ Pa·계산 압축응력65.56 MPa와 실제 응력 측정의 한계 |

`xml-fallback-checks-v2.json`에 원래 구간 ID, 절 이름, 발췌문, 원문 URL과 보존 원본 경로를 남겼다. 외부 DOI 세 링크는 웹 도구에서 접근할 수 없었다. 이는 사이트나 링크가 잘못됐다는 판정이 아니며 온라인 접근 가능 여부는 확인 불가다. 위 통과 결과는 보존 원본에서 근거를 찾을 수 있다는 의미다. 나머지 미연결 XML 문단 전체를 검증한 결과는 아니다.

## HBM2 표3~8 복원

원본 24쪽 중 해당 표가 있는 20~23쪽만 별도 PDF로 선택해 기존 Docling 2.143.0·RapidOCR 전체 페이지 OCR·TableFormer로 재추출했다. 부분 PDF의 1~4쪽과 원본 20~23쪽의 대응 및 양쪽 파일 해시를 `page-map.json`에 기록했다. 첫 제한 실행은 원인 미확정 `process_failed`로 보존했다. 같은 480초·8 GiB 제한과 자격정보를 제외한 환경의 진단 재실행은 성공했고 `hbm2-pages20-23-ocr-v2.json`에 보존했다. 기존 런타임·모델을 사용했고 설치나 전체 PDF OCR은 하지 않았다.

OCR도 요약 행 병합·기호·빈칸·열 위치 문제가 남았다. 원본 PDFium의 표 영역 텍스트와 pypdf layout의 모든 복원 행을 대조하고 20~23쪽 화면을 확인해 수정했다. 비교 과정에서 발견한 OCR 셀 불일치·누락·병합 위치 차이 126개를 원문과 맞췄다. 126개가 모두 숫자 오인식이라는 뜻은 아니다.

| 표 | 원본 쪽 | 데이터 행 | 열 | 데이터 셀 | 원문 대조 결과 |
| --- | --- | ---: | ---: | ---: | --- |
| 3 | 20 | 39 | 8 | 312 | Chip별 7개 IDD 전류와 평균±표준편차, 마지막 요약3행 보존 |
| 4 | 21 | 39 | 10 | 390 | IDD2N 측정 온도(°C)와 8개 기울기(mA/°C), 병합됐던 Odd/All 행 분리 |
| 5 | 21 | 18 | 19 | 342 | 6개 측정 루프×600/900/1200 MT/s 전류(mA), 미측정 `–` 보존 |
| 6 | 22 | 42 | 11 | 462 | 36칩 read 전류와 bank-group/bank별 열, 요약6행 보존 |
| 7 | 22 | 18 | 11 | 198 | 16칩 write 전류와 bank-group/bank별 열, 요약2행 보존 |
| 8 | 23 | 32 | 5 | 160 | Toggled DQs별 read/write 전류와 각각의 칩 수 보존 |

합계 1,864개 데이터 셀은 행 이름을 포함한다. 표5의 Slope 6개와 표8의 Slope 2개는 원래 병합 셀의 적용 열과 단위를 따로 기록하고 구간에 함께 제공했다. 표5의 `–`를 0으로 바꾸거나 Slope 값을 각 데이터율의 측정 전류로 복제하지 않았다. 캡션·열 제목·단위·Slope 문맥을 각 분할 구간에 유지했고 기존 768토큰 목표를 사용했다.

`recovered-tables.json`, `table-comparison.json`에 원문 표 위치·행·열·셀·OCR 차이와 비교 기록이 있다. 기존 보류21구간을 표별26구간으로 교체한 새 m001 판본은 99구간이며, 비대상 73구간의 텍스트는 그대로다. 기존 판본과 원본은 삭제·덮어쓰기하지 않았다.

`table_reprocessing_candidates()`는 여러 수치 열이 한 셀에 뭉친 행이 반복되는 경우 해당 표와 페이지만 재처리 대상으로 표시한다. 실제 이전 추출의 표3~8을 모두 감지했다. CLI는 이를 `reprocessing-queue.json`에 기록하고 해당 구간을 색인 후보에서 보류한다. 정상 셀과 단위가 붙은 실험 조건의 간단한 반례도 검사했다. 이는 같은 형태의 손상을 찾는 최소 검사이며 모든 OCR 오류를 검출하는 판정기는 아니다.

## ALD 표1 캡션

원본 XML 표 `materials-18-01918-t001`의 MathML `msub(a,i)`를 확인해 `with  levels for factor i`를 `with aᵢ levels for factor i`로 복원했다. 기존 41구간 중 ordinal 25의 캡션 한 곳만 바뀌고 나머지 40구간 텍스트는 같다.

문자 아래첨자도 Unicode로 보존하며 Unicode 아래첨자가 없는 문자는 `a_{q}`처럼 명시적인 표기로 남긴다. 지원하지 않는 문자라는 이유로 캡션 전체 복원을 건너뛰거나 기호를 지우지 않는다. 숫자 아래첨자·`i`·`n`·미지원 문자 `q`의 보존과 실제 캡션 수정 검사를 추가했다. 원본 XML·수정 전후·정확히 확인한 표 ID/XPath는 새 판본의 `corrections.json`에 남겼다.

## 검증과 남은 범위

관련 검사 `test_offline_preprocessing.py`, `test_document_parsers.py`는 19개 통과했다. 자동 재처리 대장과 색인 후보 보류까지 검사했다. 별도 읽기 전용 검토가 여섯 표의 1,864셀·Slope8개·원문 화면, ALD 캡션 한 곳 수정, 원본 해시·부모 판본·저장 구간 위치를 확인했으며 추가 수정 사항은 없었다.

새 두 판본 140구간의 본문 해시·실제 저장 파일 위치와 연결 ID를 확인했고 이전 run-v4 산출물 1,478개 해시는 그대로다. 새 결과의 `index-delta-candidates.jsonl`은 m001/d001 두 문헌의 검토용 대체 입력만 담으며 전체 코퍼스 재처리·색인 명령이 아니다. 다른 문헌은 기존 판본을 사용한다.

원문 재현 확인과 논문의 과학적 타당성·문헌 승인·서비스 승인은 구분했다. 새 결과도 `candidate_for_index_review`이며 승인하지 않았다. 외부 DOI의 온라인 접근성, 나머지 XML 미연결 문단의 전수 확인, 해당 표 밖의 논문 전체 의미 정확성은 남은 미확인 범위다.
