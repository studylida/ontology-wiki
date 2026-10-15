---
title: "SEMI International Standards for Smart Manufacturing & Fab Automation"
publisher: "SEMI (Semiconductor Equipment and Materials International)"
source_id: "semi_standards_and_smart_fab"
type: "official_international_standard_specification"
---

# SEMI International Standards for Smart Manufacturing & Fab Automation

글로벌 반도체 공정 장비와 팹 호스트(MES/APC/FDC) 간의 통신, 장비 상태 제어, 신뢰성 지표, 자동화 데이터 모델을 규정하는 핵심 국제 표준 규격집이다.

---

## 1. SECS/GEM 통신 및 장비 제어 모델 (The Automation Foundation)

### 1.1 SEMI E30 (GEM, Generic Equipment Model)
- **정의**: 반도체 제조 장비가 팹 호스트(Factory Host) 시스템과 통신하고 원격 제어되기 위해 반드시 구현해야 하는 표준 동작 및 상태 모델(State Model).
- **핵심 구성요소**:
  1. **Control State Model**: Offline(호스트와 단절) vs Online(호스트 통신 활성: Local 모니터링 전용 vs Remote 원격 레시피/시작 제어).
  2. **Processing State Model**: Idle(대기), Setting Up(셋업), Executing(가공 중), Paused(일시정지).
  3. **Data Collection Events (CE)**: 장비 내 상태 변경(웨이퍼 투입, 챔버 가공 완료, 밸브 개폐) 발생 시 호스트에 실시간 보고되는 이벤트.
  4. **Variables**:
     - Status Variables (SV): 센서 온도, 압력, RF 파워 등 읽기 전용 실시간 상태값.
     - Equipment Constants (EC): 호스트가 읽고 쓸 수 있는 장비 설정값.
  5. **Alarm Handling**: 장비 이상 발생 시 고유 ID 및 심각도(Alarm Set/Clear) 보고.
  6. **Recipe Management**: 가공 조건 파일(Recipe)의 호스트 업로드, 다운로드, 무결성 검증.

### 1.2 SEMI E5 (SECS-II, SEMI Equipment Communications Standard 2 Message Content)
- **정의**: 장비와 호스트 간에 교환되는 메시지의 문법과 데이터 타입(Stream & Function)을 정의.
- **주요 메시지 카테고리 (Stream)**:
  - `S1`: Equipment Status (S1F13/S1F14 Establish Communications, S1F3 Status Request).
  - `S2`: Equipment Control & Diagnostics (S2F41 Host Command - START/STOP, S2F49 Recipe Select).
  - `S5`: Exception Reporting (S5F1 Alarm Report).
  - `S6`: Data Collection (S6F11 Event Report - 장비에서 이벤트 발생 시 변수 묶음 전송).
  - `S7`: Process Program Management (레시피 송수신).

### 1.3 SEMI E37 (HSMS, High-Speed SECS Message Services)
- TCP/IP 이더넷 기반으로 SECS-II 메시지를 고속 전송하기 위한 물리/전송 계층 프로토콜(과거 RS-232 시리얼 통신 규격인 SEMI E4를 대체).

---

## 2. 객체 지향 및 고도화 장비 모델

### 2.1 SEMI E98 (OBEM, Object-Based Equipment Model)
- **목적**: 단일 챔버 장비를 넘어 다중 공정 챔버(Cluster Tool) 및 복합 모듈 장비의 내부 구조를 객체 지향적으로 표준화.
- **객체 모델 정의**:
  - `Loadport`: 웨이퍼 캐리어(FOUP) 안착 및 개폐 도어.
  - `Substrate Handling Robot`: 진공/대기 이송 로봇 및 암(Arm).
  - `Process Chamber`: 실제 화학/물리 공정이 일어나는 독립 챔버.
  - `Buffer Station`: 웨이퍼 냉각 및 대기 스테이션.

---

## 3. 지능형 공정 제어 및 이상 감지 (APC & FDC)

### 3.1 SEMI E133 (APCS, Automated Process Control Systems Interface)
- **목적**: 장비 외부의 전문 분석 엔진(APC, FDC, R2R Control)과 장비 제어기간의 실시간 데이터 교환 표준.
- **핵심 애플리케이션**:
  - **FDC (Fault Detection & Classification)**: 챔버 내부의 수십 종 센서(RF 바이어스, 가스 유량, 압력, 척 온도)를 10~100Hz 고주파로 수집하여 정상 골든 시그니처(Golden Signature)와 비교, 결함 및 설비 이상 징후 실시간 탐지.
  - **R2R (Run-to-Run) Control**: 직전 웨이퍼의 가공 결과(계측 두께, 선폭)를 피드백 받아 다음 웨이퍼의 공정 시간/파워 파라미터를 자동 보정(Feedforward / Feedback).
  - **SPC (Statistical Process Control)**: 팹 관리 상한선(UCL/LCL) 통계적 추적.

### 3.2 SEMI EDA (Equipment Data Acquisition / Interface A)
- **표준군**: SEMI E120, E125, E132, E134.
- 기존 SECS/GEM 대역폭의 한계를 극복하기 위해, 별도의 독립 기가비트 이더넷 포트를 통해 SOAP/XML, gRPC/Protobuf 기반으로 수천 Hz의 고주파 센서 데이터를 호스트 부하 없이 스트리밍 수집하는 표준.

---

## 4. 설비 신뢰성 및 생산성 평가 지표

### 4.1 SEMI E10 (RAM, Reliability, Availability, Maintainability)
- 반도체 장비의 24시간 가동 상태를 6대 기본 상태로 엄격히 분류:
  1. `Productive Time`: 정상 양산 웨이퍼 가공 시간.
  2. `Standby Time`: 장비는 정상이지만 웨이퍼나 오퍼레이터가 없어 대기하는 시간.
  3. `Engineering Time`: R&D, 엔지니어링 테스트 시간.
  4. `Scheduled Downtime`: 계획된 예방 정비(PM), 소모품 교체.
  5. `Unscheduled Downtime`: 설비 고장, 알람으로 인한 비계획 중단.
  6. `Non-Scheduled Time`: 라인 미가동 시간.

### 4.2 SEMI E79 (OEE, Overall Equipment Effectiveness)
- 설비의 종합적인 생산 효율을 측정하는 글로벌 표준 지표:
  $$\text{OEE} = \text{Availability (가용률)} \times \text{Operational Efficiency (운영 효율)} \times \text{Rate of Quality (양품률)}$$
