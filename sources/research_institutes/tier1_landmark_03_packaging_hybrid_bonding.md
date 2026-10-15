# Tier 1 분수령 논문 아카이브 03: 첨단 패키징 & 하이브리드 본딩 (Advanced Packaging & Direct Bonding)

> 본 문서는 반도체 이종 집적(Heterogeneous Integration) 및 차세대 3D 스태킹의 물리적 패러다임을 바꾼 역사적 분수령(Landmark) 논문들의 서지 정보와 공학적 핵심 원리를 수록합니다.

---

## 1. Cu-Cu Direct Bond Interconnect (DBI / Hybrid Bonding) 원조 논문 (2005 / 2015)

### [서지 정보]
- **논문명 1 (개념 증명):** Room Temperature Direct Oxide-to-Oxide Covalent Bonding and Low Temperature Metal Diffusion
- **논문명 2 (확장 논문):** 3D Integration using Direct Bond Interconnect (DBI) Technology with Sub-Micron Pitch
- **저자:** Paul M. Enquist et al. (Ziptronix / Xperi)
- **학회/저널:** IEEE Electronic Components and Technology Conference (ECTC) / International 3D Systems Integration Conference (3DIC)
- **연도:** 2005 / 2015
- **DOI / 인용:** US Patent 6,962,835 / IEEE 3DIC Best Paper Awards

### [역사적 배경 및 산업 패러다임 전환]
- **기존 방식의 한계 (Micro-bump):** 솔더 볼(Solder bump, $\mu$-bump) 기반 플립칩 접합은 피치가 $25\sim 40\ \mu\text{m}$ 이하로 줄어들 때 리플로우(Reflow) 시 솔더 브릿징(Short) 및 언더필(Underfill) 충진 불량, 열팽창계수(CTE) 미스매치로 인한 크랙이 발생하는 물리적 한계에 봉착.
- **돌파구:** 솔더를 전혀 쓰지 않고, CMP로 원자 수준의 극평탄화(RMS 거칠기 $< 0.5\ \text{nm}$)된 유전체(SiO2/SiCN)와 Cu 패드를 동시에 원자 결합시키는 DBI(Direct Bond Interconnect) 기술 창안. 피치를 $1\ \mu\text{m}$ 이하로 축소시켜 범프 대비 배선 밀도를 1,000배 이상 극대화함.

### [물리적/공학적 핵심 원리]
1. **친수성 표면 활성화 (Surface Hydrophilization):**
   - 플라즈마(Ar, $N_2, O_2$) 처리로 절연막 표면에 실란올($\text{Si-OH}$) 기를 대량 형성.
   - 상온 접촉 시 수소 결합($\text{Si-OH} \cdots \text{HO-Si}$)으로 1차 부착 유도.
   - 탈수 축합 반응($\text{Si-OH} + \text{HO-Si} \rightarrow \text{Si-O-Si} + \text{H}_2\text{O}\uparrow$)을 통해 $150\sim 200^\circ\text{C}$ 저온에서 공유 결합 형성.
2. **Cu 열팽창(Thermal Expansion) 차등 팽창 접합:**
   - Cu의 열팽창계수($\text{CTE}_{\text{Cu}} \approx 16.5\ \text{ppm/K}$)가 산화막($\text{CTE}_{\text{SiO}_2} \approx 0.5\ \text{ppm/K}$)보다 훨씬 큼.
   - CMP 단계에서 Cu 표면을 산화막 표면보다 $2\sim 5\ \text{nm}$ 미세하게 낮게 리세스(Dishing recess)시킴.
   - 어닐링($300\sim 350^\circ\text{C}$) 시 Cu가 위로 팽창하면서 상하 대향 Cu 패드가 강력한 압축 응력 하에서 원자 상호 확산(Inter-diffusion)을 일으켜 보이드 없는 금속 접합 달성.

### [산업적 영향 및 적용 팹 라인]
- 소니(Sony) 및 삼성전자 CIS(CMOS Image Sensor) 양산에 전면 도입 (픽셀층 + 로직층 적층).
- AMD 3D V-Cache (TSMC SoIC 하이브리드 본딩 공정)에 적용되어 L3 캐시 대역폭 2TB/s 돌파.
- 차세대 HBM4 및 3D SoC 로드맵의 표준 본딩 메커니즘으로 채택.

---

## 2. 팬아웃 웨이퍼 레벨 패키징 (InFO FOWLP) 논문 (2016)

### [서지 정보]
- **논문명:** Integrated Fan-Out (InFO) Wafer Level Packaging Technology for High Performance Mobile and Computing Applications
- **저자:** Chuei-Tang Chou, C. H. Yu, Doug C. H. Yu et al.
- **학회:** IEEE International Electron Devices Meeting (IEDM 2016)
- **연도:** 2016
- **DOI:** 10.1109/IEDM.2016.7838520

### [역사적 배경 및 산업 패러다임 전환]
- **기존 패키징 기판(Substrate)의 병목:** 스마트폰 AP는 전통적으로 BGA 플립칩 패키지 서브스트레이트(PCB)를 사용했으나, 기판 두께($\ge 200\ \mu\text{m}$)와 기생 인덕턴스/저항으로 인해 폼팩터 축소와 고주파 신호 무결성(Signal Integrity) 확보가 불가능했음.
- **돌파구:** PCB 기판을 완전히 제거(Substrate-less)하고, 칩 외곽 몰딩 컴파운드 영역까지 고밀도 재배선층(RDL, Redistribution Layer)을 직접 형성하는 InFO(Integrated Fan-Out) 공정 확립.

### [물리적/공학적 핵심 원리]
1. **Through InFO Via (TIV) 기술:**
   - 몰딩층을 관통하는 수직 구리 필러(Cu Post, TIV)를 도금 형성하여 패키지 상단의 DRAM과 하단의 AP 로직 칩을 최단 거리($< 100\ \mu\text{m}$)로 연결 (PoP 구조).
2. **미세 선폭 RDL 리소그래피:**
   - 폴리이미드(PI) 유전체와 Cu 세미 애디티브 공정(SAP)을 통해 $L/S = 2/2\ \mu\text{m}$ 이하의 미세 배선 구현.
   - PCB 기반 대비 패키지 두께 20% 이상 감소, 열저항 15% 개선, 고주파 신호 손실 30% 감쇄.
3. **웨이퍼 휨(Warpage) 제어:**
   - 실리콘 칩과 에폭시 몰딩 컴파운드(EMC)의 열팽창계수 불일치로 인한 캐리어 웨이퍼 휨을 보상하기 위해 잔류 응력 상쇄 유전막 엔지니어링 적용.

### [산업적 영향 및 적용 팹 라인]
- 애플(Apple) iPhone 7의 A10 Fusion 칩부터 현재 전 기종 AP 양산에 독점 적용 (TSMC 수주의 결정적 계기).
- 스마트폰 AP 고성능화 및 초박형 모바일 기기 설계의 필수 표준으로 확립.

---

## 3. 실리콘 인터포저 기반 2.5D 이종집적 (TSMC CoWoS) 논문 (2013)

### [서지 정보]
- **논문명:** A 2.5D/3D Heterogeneous Integration Platform with High-Density TSV Interposer
- **저자:** Doug C. H. Yu et al.
- **학회:** IEEE Electronic Components and Technology Conference (ECTC 2013)
- **연도:** 2013
- **DOI:** 10.1109/ECTC.2013.6575550

### [물리적/공학적 핵심 원리 및 산업적 영향]
- **실리콘 인터포저(Si Interposer):** $65\ \text{nm}$ 이하 반도체 공정을 인터포저에 적용하여 서브마이크론($0.4/0.4\ \mu\text{m}$) 미세 배선과 고밀도 관통전극(TSV) 구현.
- **CoWoS(Chip-on-Wafer-on-Substrate):** 복수의 로직 칩(GPU/ASIC)과 HBM 스택을 하나의 거대한 실리콘 인터포저 위에 마이크로범프로 나란히 실장하여 단일 칩 수준의 버스 대역폭($> 10\ \text{TB/s}$)과 극소 지연(Latency) 실현.
- **적용:** NVIDIA A100/H100/B200, Google TPU 등 전 세계 생성형 AI 가속기 하드웨어의 독점적 표준 패키징 플랫폼으로 군림.
