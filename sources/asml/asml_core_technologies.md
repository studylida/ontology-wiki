---
title: "ASML Core Technologies & Lithography Optics Systems"
publisher: "ASML Official Technical Whitepapers & Technology Documentation"
source_id: "asml_core_technologies"
type: "official_equipment_and_optical_physics_solution"
---

# ASML Core Technologies & Lithography Optics Systems

반도체 미세화의 물리적 한계를 결정짓는 글로벌 독점 노광 장비사 ASML의 광학 물리, EUV/High-NA 하드웨어 아키텍처, 계산 리소그래피, 홀리스틱 리소그래피 통합 솔루션을 규명한 엔지니어링 스냅샷이다.

---

## 1. 노광 물리학의 근본 법칙: 레일리 한계식 (Rayleigh Criterion)

반도체 회로에서 인쇄 가능한 최소 선폭(CD, Critical Dimension)은 레일리 수식에 의해 절대적으로 지배된다:

$$\text{CD} = k_1 \frac{\lambda}{\text{NA}}$$

- $\text{CD}$ (Critical Dimension): 인쇄 가능한 최소 회로 패턴 크기.
- $\lambda$ (Wavelength): 노광에 사용되는 광원의 파장.
- $\text{NA}$ (Numerical Aperture, 개구수): 렌즈/반사경 광학계가 빛을 모으는 각도 범위 ($\text{NA} = n \sin\theta$).
- $k_1$ (Process Factor): 레지스트 특성, 마스크 기술, 조명계 최적화 수준을 반영하는 공정 상수 (물리적 이론 한계 $0.25$).

### 1.1 ASML의 세 가지 스케일링 축
1. **파장 단축 ($\lambda \downarrow$)**: 
   - DUV(ArF 액침, 193nm)에서 극자외선 EUV(13.5nm)로 전환 (파장 1/14로 급감).
2. **개구수 확대 ($\text{NA} \uparrow$)**: 
   - 0.33 NA(표준 EUV, NXE 플랫폼)에서 0.55 NA(High-NA EUV, EXE 플랫폼)로 전환 (단일 노광 8nm 해상도 구현).
3. **공정 상수 개선 ($k_1 \downarrow$)**: 
   - 계산 리소그래피(OPC, SMO) 및 다층막 위상 제어를 통해 $k_1$을 물리적 한계점인 0.28 수준까지 근접.

---

## 2. 극자외선 (EUV) 노광 광학계 아키텍처

13.5nm 파장의 EUV 광선은 대기(질소, 산소) 및 기존 굴절 유리 렌즈에 100% 흡수되므로, 완전히 새로운 물리적 아키텍처가 요구된다.

### 2.1 LPP (Laser-Produced Plasma) 극자외선 광원 메커니즘
- 진공 챔버 내에서 초당 50,000개의 고순도 주석(Sn) 액적(Droplet, 직경 약 25㎛)을 고속 분사.
- 20~30kW급 고출력 $CO_2$ 레이저를 액적당 2회 타격:
  1. `Prepulse (사전 펄스)`: 주석 방울을 납작한 팬케이크 모양으로 팽창시킴.
  2. `Main pulse (주 펄스)`: 고에너지 충격파로 주석을 수십만 도의 고온 플라즈마 상태로 기화시켜 13.5nm EUV 광선 방출.
- 집광 거울(Collector Mirror)을 통해 플라즈마에서 방출된 EUV 빛을 중간 초점(IF, Intermediate Focus)으로 집속.

### 2.2 전반사 몰리브덴/실리콘(Mo/Si) 브래그 반사경 (Bragg Multilayer Optics)
- 빛이 유리를 투과할 수 없으므로, 독일 자이스(Carl Zeiss)와 공동 개발한 **다층막 반사 거울**만을 사용.
- 몰리브덴(Mo, 굴절률 낮음)과 실리콘(Si, 굴절률 높음)을 원자층 단위로 40~50쌍 정밀 교차 증착.
- 거울 단일 매수당 반사율은 약 70% 수준이며, 스캐너 내부의 10여 개 반사경을 거치면 웨이퍼에 도달하는 광량은 초기 광원의 약 1~2%로 급감하므로 고출력 광원(300W~500W 이상) 기술이 필수적임.

### 2.3 펠리클 (Pellicle) 보호막
- 마스크 표면에 먼지/파티클이 앉는 것을 방지하는 투과성 보호막.
- 13.5nm 빛을 90% 이상 투과시키면서 고열(수백 도) 플라즈마 복사열을 견디기 위해 탄소나노튜브(CNT) 또는 초박막 금속 실리사이드 소재 채택.

---

## 3. 차세대 High-NA EUV (0.55 NA, EXE 플랫폼) 기술 혁신

### 3.1 0.55 NA의 물리적 난제: 마스크 섀도잉 (Mask Shadowing)
- 개구수를 0.33에서 0.55로 키우면 광학계로 들어가는 빛의 입사각이 커져, 마스크 위의 3차원 흡수체 패턴(Cr/Ta/Ru)에 의해 인접 패턴에 그림자가 생기는 **마스크 섀도잉 현상** 발생.

### 3.2 아나모픽(Anamorphic) 광학계 도입
- 그림자 효과를 극복하기 위해 축소 투영 배율을 수평과 수직으로 비대칭 설계:
  - **X축 (수평)**: 4배 축소
  - **Y축 (수직)**: 8배 축소
- 배율 비대칭으로 인해 노광 필드 크기가 절반(Half Field, 26mm × 16.5mm)으로 줄어들며, 이를 보상하기 위해 스캔 스테이지의 가속도를 극대화(과거 대비 4배 가속)하여 웨이퍼 시간당 생산성(Throughput, 150~220wph)을 유지.

---

## 4. 계산 리소그래피 (Computational Lithography)

빛의 회절 한계에 도달한 극미세 패턴은 원래 마스크 형태대로 웨이퍼에 인쇄되지 않고 왜곡(모서리 라운딩, 선폭 축소)된다.

- **OPC (Optical Proximity Correction, 광학 근접 효과 보정)**:
  - 빛의 간섭/회절 방정식을 역산하여, 마스크 패턴의 모서리에 세리프(Serif)를 붙이거나 보조 피처(SBAR, Sub-Resolution Assist Features)를 추가하여 웨이퍼 표면에는 완벽한 사각형이 전사되도록 사전 왜곡 설계.
- **SMO (Source-Mask Optimization)**:
  - 특정 회로 패턴에 최적화된 맞춤형 조명 동공(Pupil) 형태(다이폴, 쿼드러폴 등)와 마스크 형상을 수학적 알고리즘으로 동시 합성.

---

## 5. 홀리스틱 리소그래피 (Holistic Lithography) & YieldStar

ASML의 경쟁력은 단순 스캐너 하드웨어에 머무르지 않고, **스캐너 + 계측(Metrology) + 소프트웨어(Computational)**가 폐루프(Closed-Loop)로 연동되는 데 있다.

- **TWINSCAN 듀얼 웨이퍼 스테이지**:
  - 웨이퍼 A가 노광되는 동안, 웨이퍼 B는 인접 스테이지에서 서브 나노미터 정밀도로 웨이퍼 표면 높낮이 맵(Topography)과 정렬 마크(Alignment Marks)를 사전 스캔.
- **YieldStar 회절 기반 오버레이 (DBO, Diffraction-Based Overlay)**:
  - 인라인 상에서 웨이퍼 상하 층간 정렬 오차(Overlay Error)를 수 초 만에 측정하여, 스캐너 스테이지로 실시간 보정 파라미터(Offset Correction)를 피드백(R2R Loop).
