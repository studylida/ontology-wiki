---
title: "Tier 1 Landmark Papers: Memory Architecture (BiCS, V-NAND TCAT, PUC, HBM)"
publisher: "IEEE IEDM, IEEE ISSCC, Toshiba/Kioxia, Samsung Electronics, SK hynix"
source_id: "tier1_landmark_02_memory_3dnand_hbm"
tier: "Tier-1 Landmark Milestone"
---

# Tier 1 Landmark Papers: Memory Architecture Revolution

메모리 반도체를 평면(2D) 한계에서 3차원 수직 적층(3D NAND) 및 초고대역폭(HBM)으로 대전환시킨 4대 기념비적 논문 아카이브이다.

---

### [LM-06] 3D NAND의 기원: BiCS 기술 최초 제안 (2007 IEDM)
- **논문명**: *Bit Cost Scalable Technology with Punch and Plug Process for Ultra High Density Flash Memory*
- **저자/기관**: H. Tanaka, M. Kido, K. Yahashi, M. Oomura, R. Katsumata, et al. (Toshiba Corporation / 현 Kioxia)
- **학회/발표**: IEEE International Electron Devices Meeting (IEDM 2007), DOI: 10.1109/IEDM.2007.4418913
- **해결한 물리적 한계**:
  - 2D 평면 낸드에서 셀 간격이 15nm 이하로 좁아짐에 따른 인접 셀 간 기생 정전용량 누설(Cross-talk) 및 플로팅 게이트 전하 누설 한계.
- **공학적 해결책 및 공정 (Punch and Plug)**:
  - 게이트 전극 층과 절연막 층을 다층으로 먼저 일괄 증착한 뒤, **단 한 번의 식각으로 수직 관통 홀(Memory Hole)을 뚫고(Punch), 그 안에 실리콘 채널과 산화막-질화막-산화막(ONO)을 채워 넣는(Plug)** 파괴적 혁신 공법 제안.
- **산업적 파급 효과**: 개별 셀 패터닝 비용이 적층 단수에 비례하지 않고 일정하게 유지되는 "비트당 비용 절감(Bit Cost Scalable)" 패러다임을 확립하여 전 세계 낸드플래시 양산 방식을 영구히 변경함.

---

### [LM-07] 3D V-NAND 최초 상용 양산화: TCAT 실증 (2009 VLSI / 2013 IEDM)
- **논문명**: *A Highly Manufacturable 3D NAND Flash Memory Technology with Charge Trap Cell (TCAT)*
- **저자/기관**: J. Jang, H-S. Kim, W. Cho, H. Cho, J. Kim, et al. (삼성전자 반도체연구소 메모리사업부)
- **학회/발표**: IEEE Symposium on VLSI Technology (2009) / IEEE IEDM (2013)
- **해결한 물리적 한계**:
  - 플로팅 게이트(도체)의 전하 누설 및 식각 종횡비 한계를 극복하기 위해, 절연체인 실리콘 질화막($Si_3N_4$)의 깊은 트랩 준위에 전자를 비휘발성으로 포획하는 **CTF (Charge Trap Flash)** 기술을 3차원 원통형 게이트(GAA 형상)와 결합.
- **정량 실측 데이터**: 
  - 2D 낸드 대비 쓰기(Program) 속도 **2배 이상 향상**, 소비 전력 **50% 이상 절감**, 쓰기 내구성(Endurance) **10배 이상 향상(30,000회 이상)**.
- **산업적 파급 효과**: 삼성전자가 2013년 8월 세계 최초로 1세대 24단 3D V-NAND 양산 출하에 성공하며 세계 최초의 3차원 메모리 상용화 시대를 개막함.

---

### [LM-08] 4D NAND: Peri-Under-Cell (PUC) 구조 실증 (2018 IEDM)
- **논문명**: *Highly Manufacturable and Cost-Effective 96-Layer 3D NAND Flash Memory with Peri Under Cell (PUC) Technology*
- **저자/기관**: SK하이닉스 낸드개발본부 연구팀
- **학회/발표**: IEEE International Electron Devices Meeting (IEDM 2018)
- **해결한 물리적 한계**:
  - 기존 3D 낸드에서 주변부 구동 회로(Peripheral Circuit, 센스앰프 및 로우 디코더)가 메모리 셀 어레이 옆에 평면으로 배치되어 다이(Die) 면적의 20~30%를 불필요하게 낭비하던 풋프린트 한계.
- **공학적 해결책**:
  - 기판 위에 페리 회로를 먼저 만들고, 그 위에 절연막을 덮은 뒤 메모리 셀 어레이를 옥상처럼 올려 쌓는 **PUC (Peri-Under-Cell)** 구조 완성.
- **정량 실측 데이터**: 동일 웨이퍼 한 장당 생산 가능한 정상 칩 수(Net Die) **30% 이상 증가**, 칩 사이즈 축소로 생산성 극대화.

---

### [LM-09] 세계 최초의 HBM 실증 (2014 ISSCC)
- **논문명**: *A 1.2V 8Gb 128GB/s High-Bandwidth Memory (HBM) DRAM with TSV and 2.5D Interposer*
- **저자/기관**: D. U. Lee, K. W. Kim, K. W. Park, H. J. Kim, J. H. Cho, et al. (SK하이닉스 & AMD)
- **학회/발표**: IEEE International Solid-State Circuits Conference (ISSCC 2014), DOI: 10.1109/ISSCC.2014.6757501
- **해결한 물리적 한계**:
  - 기존 DDR3/GDDR5 인터페이스의 협소한 32비트/64비트 버스 폭과 보드 배선의 기생 인덕턴스로 인한 메모리 전송 속도 한계(폰 노이만 메모리 벽, Memory Wall).
- **공학적 해결책 및 회로 아키텍처**:
  - 4개의 2Gb DRAM 다이를 실리콘 관통 전극(TSV)으로 수직 관통하여 1024비트의 초광대역 버스 폭(Wide I/O)을 구축하고, 실리콘 인터포저 위에서 GPU와 직접 2.5D 병렬 연결.
- **정량 실측 데이터**:
  - 작동 전압 **1.2V**, 대역폭 **128 GB/s** (당시 최고속 GDDR5 대비 대역폭 4배 이상, 대역폭당 전력 효율 2배 이상 우수).
- **산업적 파급 효과**: 현재 전 세계 AI 가속기(NVIDIA H100/B200 등)의 핵심 필수 부품인 HBM의 산업 표준(JEDEC)과 양산 시초를 정립함.
